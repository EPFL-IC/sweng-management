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

"""SwEng management commands."""

__author__ = "stefan.bucur@epfl.ch (Stefan Bucur)"


import shutil
import os
import shlex
import subprocess
import tempfile
import yaml

from swengmgmt import epfl
from swengmgmt import github
from swengmgmt import spreadsheets
from swengmgmt import students
from swengmgmt import util


class Command(object):
    """A generic SwEng command."""

    def __init__(self):
        self.args = None
        self.config = {}
        self.auth_config = {}

    def execute(self, args):
        self.args = args

        if os.path.exists(args.config):
            with open(args.config, "r") as f:
                self.config = yaml.load(f)

        if os.path.exists(args.auth):
            with open(args.auth, "r") as f:
                self.auth_config = yaml.load(f)

    def finalize(self):
        if not self.args:
            return
        with open(self.args.auth, "w") as f:
            yaml.dump(self.auth_config, stream=f, default_flow_style=False)


class SwengClassCommand(Command):
    """A command that requires access to the SwEng class information."""

    def __init__(self):
        super(SwengClassCommand, self).__init__()

        self.student_sheet = None
        self.team_sheet = None
        self.sweng_class = None

    def execute(self, args):
        super(SwengClassCommand, self).execute(args)

        gdata_auth = spreadsheets.GDataOAuthProvider(self.config,
                                                     self.auth_config)
        gdata_auth.authenticate(args.non_interactive)
        google_client = gdata_auth.getClient()

        self.student_sheet = spreadsheets.SwEngStudentSpreadsheet(
            google_client,
            self.config["spreadsheet"]["title"],
            self.config["spreadsheet"]["students_worksheet"])

        self.team_sheet = spreadsheets.SwEngTeamSpreadsheet(
            google_client,
            self.config["spreadsheet"]["title"],
            self.config["spreadsheet"]["teams_worksheet"])

        self.sweng_class = students.SwEngClass(self.config)
        self.sweng_class.populateFromSpreadsheet(self.student_sheet,
                                                 self.team_sheet)
        
    @classmethod
    def confirmClassOperation(cls):
        answer = None
        while answer not in ["yes", "no"]:
            answer = raw_input("This operation affects most or the entire class. "
                               "Are you sure you want to proceed? "
                               "Type 'yes' or 'no'.")
        return answer == "yes"


class GithubCommand(SwengClassCommand):
    """A command that requires access to Github."""

    def execute(self, args):
        super(GithubCommand, self).execute(args)

        github_auth = github.GithubAuthProvider(self.config,
                                                self.auth_config)
        github_auth.authenticate(args.non_interactive)
        github_client = github_auth.getClient()

        # TODO: Let the class object figure this out
        self.github_org = github_client.organization(
            self.config["organization"]["name"])
        self.sweng_class.updateGithubData(self.github_org)


class StudentsListCommand(GithubCommand):
    """List registered students."""

    arg_name = "students-list"

    def register(self, parser):
        parser.add_argument("-f", "--format", choices=["items", "tabular"],
                            default="items")
        parser.add_argument("--exclude", nargs="*",
                            help="A list of students to exclude.")
        parser.add_argument("students", nargs="*",
                            help="A list of students to consider. "
                            "Leave empty to include everyone.")

    def _printItemized(self, student_list):
        for student in student_list:
            print util.bold(str(student))
            print "  Team: %s" % util.red_if_none(student.team_name)
            print "  Github ID: %s" % util.red_if_none(student.github_id)
            if student.team:
                print "  Team Clone URL: %s" % util.red_if_none(student.team.repo_ssh_url)
            print "  Exam Clone URL: %s" % util.red_if_none(student.repo_ssh_url)
            print "  Exam access: %s" % util.red_if_none(util.red_green(
                student.repo_access, "pull", "push"))
            print

    def _printTabular(self, student_list):
        data = []
        column_widths = {}

        header = [
            ("name", "Name"),
            ("gaspar", "Gaspar"),
            ("sciper", "SCIPER"),
            ("team", "Team"),
            ("exam-access", "Exam Access"),
        ]
        header_dict = dict(header)

        for student in student_list:
            entry = {
              "name": student.name,
              "gaspar": student.gaspar,
              "sciper": student.sciper,
              "team": student.team_name,
              "exam-access": student.repo_access,
            }
            data.append(entry)

            for key, value in entry.iteritems():
                column_widths[key] = max(column_widths.get(key,
                                                           len(header_dict[key])),
                                         len(value or "N/A"))

        for key, title in header:
            print " %s" % title.ljust(column_widths[key]),
        print
        for key, title in header:
            print " %s" % ("=" * column_widths[key]),
        print
        for entry in data:
            for key, _ in header:
                print " %s" % (entry[key] or "N/A").ljust(column_widths[key]).encode("utf-8"),
            print

    def execute(self, args):
        super(StudentsListCommand, self).execute(args)

        query = students.StudentQuery(args.students, args.exclude)
        student_list = self.sweng_class.findStudents(query)
        if args.format == "items":
            self._printItemized(student_list)
        elif args.format == "tabular":
            self._printTabular(student_list)

class StaffPermCommand(GithubCommand):
    arg_name = "staff-perm"

    def register(self, parser):
        parser.add_argument("permission", choices=["push", "pull"],
                            help="The permission to set.")

    def execute(self, args):
        super(StaffPermCommand, self).execute(args)
        self.sweng_class.changeStaffPermissions(
            github_org=self.github_org, permission=args.permission)

class StudentsPermCommand(GithubCommand):
    """Update student permissions."""

    arg_name = "students-perm"

    def register(self, parser):
        parser.add_argument("--exclude", nargs="*",
                            help="A list of students to exclude.")
        parser.add_argument("permission", choices=["push", "pull"],
                            help="The permission to set.")
        parser.add_argument("students", nargs="*",
                            help="A list of students to consider. "
                            "Leave empty to include everyone.")

    def execute(self, args):
        if not (args.students or self.confirmClassOperation()):
            return
        
        super(StudentsPermCommand, self).execute(args)
        
        query = students.StudentQuery(args.students, args.exclude)
        student_list = self.sweng_class.findStudents(query)
        
        for student in student_list:
            student.updateTeamPermission(args.permission)

class StudentsHideCommand(GithubCommand):
    """Hide the student's repository, if it exists, by removing them as a collaborator."""

    arg_name = "students-hide"

    def register(self, parser):
        parser.add_argument("--exclude", nargs="*",
                    help="A list of students to exclude.")
        parser.add_argument("students", nargs="*",
                            help="A list of students to consider. "
                            "Leave empty to include everyone.")

    def execute(self, args):
        if not (args.students or self.confirmClassOperation()):
            return

        super(StudentsHideCommand, self).execute(args)

        query = students.StudentQuery(args.students, args.exclude)
        student_list = self.sweng_class.findStudents(query)

        for student in student_list:
            self.sweng_class.hideExamRepo(student, self.github_org)

class StudentsCreateCommand(GithubCommand):
    """Create exam repos for students."""

    arg_name = "students-create"

    def register(self, parser):
        parser.add_argument("--exclude", nargs="*",
                            help="A list of students to exclude.")
        parser.add_argument("students", nargs="*",
                            help="A list of students to consider. "
                            "Leave empty to include everyone.")

    def execute(self, args):
        super(StudentsCreateCommand, self).execute(args)
        
        query = students.StudentQuery(args.students, args.exclude)
        student_list = self.sweng_class.findStudents(query)
        
        for student in student_list:
            self.sweng_class.createExamRepo(student, self.github_org)

class StudentsPopulateCommand(GithubCommand):
    """Force push a given repository to students' exam repositories"""

    arg_name = "students-populate"

    def register(self, parser):
        parser.add_argument("--exclude", nargs="*",
                            help="A list of students to exclude.")
        parser.add_argument("--clone", required=True,
                            help="The repo repository to clone into all student repositories.")
        parser.add_argument("students", nargs="*",
                            help="A list of students to consider. "
                            "Leave empty to include everyone.")

    def clone_repo(self, clone_url, local_dir):
        with util.cd(local_dir):
            subprocess.check_call(shlex.split("git clone {url} clone_source".format(
                local_dir=local_dir, url=clone_url
            )))
        return "{dir}/clone_source".format(dir=local_dir)

    def execute(self, args):
        super(StudentsPopulateCommand, self).execute(args)
        query = students.StudentQuery(args.students, args.exclude)
        student_list = self.sweng_class.findStudents(query)

        clone_dir = tempfile.mkdtemp()
        try:
            repo_path = self.clone_repo(clone_url=args.clone, local_dir=clone_dir)
            for student in student_list:
                self.sweng_class.cloneRepo(repo_path=repo_path,
                                           student=student, github_org=self.github_org)
        finally:
            shutil.rmtree(clone_dir, ignore_errors=True)


class StudentsDeleteCommand(GithubCommand):
    """[DANGEROUS] Delete the exam repos of students."""

    arg_name = "students-delete"

    def register(self, parser):
        pass

    def execute(self, args):
        pass


class TeamsListCommand(GithubCommand):
    """List registered teams."""

    arg_name = "teams-list"

    def register(self, parser):
        pass

    def execute(self, args):
        pass


class TeamsPermCommand(GithubCommand):
    """Update teams permissions."""

    arg_name = "teams-perm"

    def register(self, parser):
        parser.add_argument("--exclude", nargs="*",
                            help="A list of teams to exclude.")
        parser.add_argument("permission", choices=["push", "pull"],
                            help="The permission to set.")
        parser.add_argument("teams", nargs="*",
                            help="A list of teams to consider. "
                            "Leave empty to include everyone.")

    def execute(self, args):
        if not (args.teams or self.confirmClassOperation()):
            return
        
        super(TeamsPermCommand, self).execute(args)
        
        query = students.TeamQuery(args.teams, args.exclude)
        team_list = self.sweng_class.findTeams(query)
        
        for team in team_list:
            team.updateTeamPermission(args.permission)


class TeamsCreateCommand(GithubCommand):
    """Create homework repos for teams."""

    arg_name = "teams-create"

    def register(self, parser):
        parser.add_argument("--exclude", nargs="*",
                            help="A list of teams to exclude.")
        parser.add_argument("teams", nargs="*",
                            help="A list of teams to consider. "
                            "Leave empty to include everyone.")

    def execute(self, args):
        super(TeamsCreateCommand, self).execute(args)
        
        query = students.TeamQuery(args.teams, args.exclude)
        team_list = self.sweng_class.findTeams(query)
        
        for team in team_list:
            self.sweng_class.createTeamRepo(team, self.github_org)


class TeamsDeleteCommand(GithubCommand):
    """[DANGEROUS] Delete the homework repos of teams."""

    arg_name = "teams-delete"

    def register(self, parser):
        pass

    def execute(self, args):
        pass


class RepairCommand(SwengClassCommand):
    """Repair the students spreadsheet."""

    arg_name = "repair"

    def register(self, parser):
        pass

    def execute(self, args):
        super(RepairCommand, self).execute(args)

        ldap_object = epfl.EPFL_LDAP()
        self.student_sheet.repair(ldap_object)


class ClassOpen(GithubCommand):
    """Open all team repositories to everyone."""

    arg_name = "class-open"

    def register(self, parser):
        pass

    def execute(self, args):
        super(ClassOpen, self).execute(args)
        self.sweng_class.openTeamReposToClass(self.github_org)


class ClassClose(GithubCommand):
    """Hide all team repositories from everyone."""

    arg_name = "class-close"

    def register(self, parser):
        pass

    def execute(self, args):
        super(ClassClose, self).execute(args)
        self.sweng_class.closeTeamReposToClass(self.github_org)


class ClassCreate(GithubCommand):
    """Add all the students to an all-class team."""

    arg_name = "class-create"

    def register(self, parser):
        parser.add_argument("--exclude", nargs="*",
                            help="A list of students to exclude.")
        parser.add_argument("students", nargs="*",
                        help="A list of students to consider. "
                             "Leave empty to include everyone.")

    def execute(self, args):
        super(ClassCreate, self).execute(args)

        query = students.StudentQuery(args.students, args.exclude)
        student_list = self.sweng_class.findStudents(query)

        for student in student_list:
            self.sweng_class.addStudentToClassTeam(student, self.github_org)

ALL_COMMANDS = [StudentsListCommand, StudentsPermCommand, StudentsCreateCommand,
                StudentsDeleteCommand, TeamsListCommand, TeamsPermCommand,
                TeamsCreateCommand, TeamsDeleteCommand, RepairCommand,
                ClassOpen, ClassClose, ClassCreate, StaffPermCommand,
                StudentsHideCommand, StudentsPopulateCommand]


def registerGlobalArguments(parser):
    parser.add_argument("-c", "--config", default="config.yaml",
                        help="The configuration file to use. "
                        "Relative paths are appended to the script directory.")
    parser.add_argument("-a", "--auth", default="auth.yaml",
                        help="The authentication cache file to use. "
                        "Relative paths are appended to the script directory.")
    parser.add_argument("-d", "--debug", action="store_true",
                        default=False,
                        help="More verbose logging of actions")
    parser.add_argument("-n", "--non-interactive", action="store_true",
                        default=False,
                        help="Refrain from requesting user input.  Useful when "
                        "using the command in batch mode.")


def registerCommands(parser, commands):
    subparsers = parser.add_subparsers(help="The operation to perform on the class")

    for command in commands:
        cmd_inst = command()
        subparser = subparsers.add_parser(command.arg_name,
                                          help=command.__doc__)
        cmd_inst.register(subparser)
        subparser.set_defaults(command=cmd_inst)
