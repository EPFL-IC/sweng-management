#!/usr/bin/env python
#
# This file is part of the sweng-management tool.
#
# sweng-management is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

"""Student management."""


import logging
import re

from swengmgmt import epfl


class GithubEntity(object):
    """Mix-in for Github data manipulation."""

    @property
    def repo_ssh_url(self):
        return self.gh_repo.ssh_url if self.gh_repo else None

    @property
    def repo_name(self):
        return self.gh_repo.name if self.gh_repo else None

    @property
    def repo_access(self):
        return self.gh_team.permission if self.gh_team else None

    def updateTeamPermission(self, permission):
        if permission == self.gh_team.permission:
            return

        self.gh_team.edit(self.gh_team.name,
                          permission)
        logging.info("%s has now %s access to their repository"
                     % (self, permission))

    def eraseGithubData(self):
        if not self.gh_team:
            logging.info("%s does not have a team. Skipping." % self)
        else:
            if self.gh_team.delete():
                self.gh_team = None
                logging.info("Deleted team for %s." % self)
            else:
                logging.info("Could not delete team for %s. Skipping." % self)

        if not self.gh_repo:
            logging.info("%s does not have a repo. Skipping." % self)
        else:
            if self.gh_repo.delete():
                self.gh_repo = None
                logging.info("Deleted repo for %s." % self)
            else:
                logging.info("Could not delete repo for %s. Skipping." % self)


class SwEngStudent(epfl.EPFLStudentData, GithubEntity):
    def __init__(self, team_name=None, github_id=None, **kwargs):
        super(SwEngStudent, self).__init__(**kwargs)

        self.team_name = team_name
        self.team = None
        self.github_id = github_id

        self.gh_team = None
        self.gh_repo = None


class SwEngTeam(GithubEntity):
    def __init__(self, name=None, github_slug=None):
        super(SwEngTeam, self).__init__()

        self.name = name
        self.github_slug = github_slug
        self.students = []

        self.gh_team = None
        self.gh_repo = None

    def __unicode__(self):
        return self.name

    def __str__(self):
        return unicode(self).encode("utf-8")


class Query(object):
    def __init__(self, search_terms=None, exclude_list=None):
        self._search_terms = [term.lower() for term
                              in search_terms] if search_terms else None

        self._exclude = set([term.lower() for term
                             in exclude_list]) if exclude_list else None

    def _match(self, entity, search_term):
        return True

    def match(self, entity):
        if self._exclude:
            for search_term in self._exclude:
                if self._match(entity, search_term):
                    return False
        if self._search_terms:
            for search_term in self._search_terms:
                if self._match(entity, search_term):
                    return True
            return False
        return True


class StudentQuery(Query):
    def _match(self, entity, search_term):
        return (search_term == str(entity.sciper).lower() or
                search_term == entity.gaspar.lower() or
                search_term == entity.email.lower() or
                search_term == entity.github_id.lower() or
                search_term in entity.name.lower())


class TeamQuery(Query):
    def _match(self, entity, search_term):
        return (search_term == entity.github_slug.lower() or
                search_term in entity.name.lower())


class SwEngClass(object):
    STUDENT_TEAM_FMT = "%s%s (%s)"

    def __init__(self, config):
        self._org_config = config["organization"]
        self.teams = {}
        self.students = {}

        self._student_team_re = re.compile(
            "".join([re.escape(self._org_config["exam-team-prefix"]),
                     r"(.*) \((.*)\)"]))
        self._student_repo_re = re.compile(
            "".join([re.escape(self._org_config["exam-repo-prefix"]),
                     r"(.*)"]))
        self._team_re = re.compile(
            "".join([re.escape(self._org_config["homework-team-prefix"]),
                     r"(.*)"]))
        self._team_repo_re = re.compile(
            "".join([re.escape(self._org_config["homework-repo-prefix"]),
                     r"(.*)"]))

    def changeStaffPermissions(self, github_org, permission):
        staff_team = github_org.team(self._org_config["staff-team-id"])
        staff_team.edit(name=staff_team.name,
                        permission=permission)

    def populateFromSpreadsheet(self, student_sheet, team_sheet):
        student_list = student_sheet.getStudentList(SwEngStudent)
        self.students = { student.gaspar: student for student in student_list }

        team_list = team_sheet.getTeamList(SwEngTeam)
        self.teams = { team.name: team for team in team_list }

        for student in student_list:
            if not student.team_name:
                continue

            student.team = self.teams[student.team_name]
            student.team.students.append(student)

    def updateFromLDAP(self, ldap_object):
        """Update the student entries with data from the given LDAP object."""

        for student in self.students.itervalues():
            try:
                ldap_object.lookup(student)
            except epfl.StudentNotFoundError:
                logging.warning("Could not find student %s. Skipping" % student)

    def findStudents(self, query):
        result = []
        for student in self.students.itervalues():
            if query.match(student):
                result.append(student)
        return result

    def findTeams(self, query):
        result = []
        for team in self.teams.itervalues():
            if query.match(team):
                result.append(team)
        return result

    # TODO: Consolidate the two calls below, to avoid extra API calls

    def _updateStudentGithubData(self, github_org):
        for gh_team in github_org.iter_teams():
            match = self._student_team_re.match(gh_team.name)
            if not match:
                continue
            student = self.students[match.group(1)]
            student.gh_team = gh_team

        for gh_repo in github_org.iter_repos():
            match = self._student_repo_re.match(gh_repo.name)
            if not match:
                continue
            student = self.students[match.group(1)]
            student.gh_repo = gh_repo

    def _updateTeamGithubData(self, github_org):
        teams_by_slug = { team.github_slug: team
                         for team in self.teams.itervalues() }

        for gh_team in github_org.iter_teams():
            match = self._team_re.match(gh_team.name)
            if not match:
                continue
            team = self.teams[match.group(1)]
            team.gh_team = gh_team

        for gh_repo in github_org.iter_repos():
            match = self._team_repo_re.match(gh_repo.name)
            if not match:
                continue
            team = teams_by_slug[match.group(1)]
            team.gh_repo = gh_repo

    def updateGithubData(self, github_org):
        self._updateStudentGithubData(github_org)
        self._updateTeamGithubData(github_org)

    def createTeamRepo(self, team, github_org):
        # Create the repo
        if not team.gh_repo:
            team.gh_repo = github_org.create_repo(
                "".join([self._org_config["homework-repo-prefix"], team.github_slug]),
                private=True)

        github_org.team(self._org_config["staff-team-id"]).add_repo(
            team.gh_repo.full_name)

        # Create the Github team
        if not team.gh_team:
            team.gh_team = github_org.create_team(
                "".join([self._org_config["homework-team-prefix"], team.name]),
                permissions='push')

        team.gh_team.add_repo(team.gh_repo.full_name)

        # Populate the Github team
        for student in team.students:
            if team.gh_team.invite(student.github_id):
                logging.info("Added %s (%s) to team %s."
                             % (student.github_id, student, team))
            else:
                logging.info("Skipping %s (%s)." % (student.github_id, student))
        valid_github_ids = set(student.github_id.lower()
                               for student in team.students)
        for member in team.gh_team.iter_members():
            if member.login.lower() not in valid_github_ids:
                team.gh_team.remove_member(member.login)
                logging.info("Removed %s from team %s." % (member.login, team))

        team.gh_team.edit(team.gh_team.name, permission='push')

    def createExamRepo(self, student, github_org):
        # Create the repo
        if not student.gh_repo:
            student.gh_repo = github_org.create_repo(
                "".join([self._org_config["exam-repo-prefix"], student.gaspar]),
                private=True)
            github_org.team(self._org_config["staff-team-id"]).add_repo(
                student.gh_repo.full_name)
            logging.info("Created exam repo for student %s." % student)
        else:
            logging.info("Exam repo already exists for student %s. Skipping."
                         % student)
            
        # Create the GitHub team
        if not student.gh_team:
            student.gh_team = github_org.create_team(
                "".join([self._org_config["exam-team-prefix"], student.gaspar,
                         " (%s)" % student.name]),
                permission="push")

            logging.info("Created exam team for student %s." % student)

        if not student.gh_team.has_repo(student.gh_repo.full_name):
            student.gh_team.add_repo(student.gh_repo.full_name)

        # Populate the Github team
        if student.gh_team.invite(student.github_id):
            logging.info("Added %s (%s) to his/her exam repo."
                         % (student.github_id, student))

        for member in student.gh_team.iter_members():
            if member.login.lower() != student.github_id.lower():
                student.gh_team.remove_member(member.login)
                logging.info("Removed %s from exam repo %s"
                             % (member.login, student))

    def openTeamReposToClass(self, github_org):
        class_team = github_org.team(self._org_config["class-team-id"])

        for team in self.teams.itervalues():
            for student in team.students:
                class_team.invite(student.github_id)
            class_team.add_repo(team.gh_repo.full_name)

    def closeTeamReposToClass(self, github_org):
        class_team = github_org.team(self._org_config["class-team-id"])

        for team in self.teams.itervalues():
            class_team.remove_repo(team.gh_repo.full_name)
            for student in team.students:
                class_team.remove_member(student.github_id)
