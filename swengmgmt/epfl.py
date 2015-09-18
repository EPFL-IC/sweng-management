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

"""EPFL student directory."""


import ldap
import re

# TODO: Move this in a configuration
LDAP_HOST = "ldap://ldap.epfl.ch"


class EPFLStudentData(object):
    """Encode basic EPFL student information."""

    def __init__(self, name=None, email=None, gaspar=None, sciper=None):
        self.name = name
        self.email = email
        self.gaspar = gaspar
        self.sciper = sciper

    def __unicode__(self):
        return "[%s/%s] %s <%s>" % (self.gaspar or "-",
                                    self.sciper or "-",
                                    self.name or "-",
                                    self.email or "-")

    def __str__(self):
        return unicode(self).encode("utf-8")


class StudentError(Exception):
    """Generic LDAP error."""
    pass


class StudentNotFoundError(StudentError):
    """Student wasn't found in LDAP."""
    pass


class StudentUndefinedError(StudentError):
    """Not enough information about student."""
    pass


class EPFL_LDAP(object):
    scope = 'o=epfl,c=ch'
    default_filter = ['displayName', 'mail', 'uid', 'uniqueIdentifier']

    def __init__(self):
        self.ldap_obj = ldap.initialize(LDAP_HOST)

    def pick_best_result(self, results):
        """
        The only hack this covers is when students have multiple 'uid' (i.e. GASPAR) logins.
        This happens when the user is GASPAR@FOO, where FOO is usually a unit. This only
        happens once in a while, but this takes care of those weird results.

        This primarily happens when the result is from a lookup based on sciper number.
        :param results: The list of MULTIPLE RESULTS from lookup
        :return: a single "best" result
        """
        first = results[0]
        first[1]['uid'] = [re.search("^([a-z]+)(?:@.*)?$", first[1]['uid'][0]).group(1)]
        return [first]

    def lookup(self, student_data):
        """Refresh a data object for a student from the LDAP directory."""

        if student_data.gaspar:
            query = '(uid=%s)' % student_data.gaspar
        elif student_data.sciper:
            query = '(uniqueIdentifier=%s)' % student_data.sciper
        elif student_data.email:
            query = '(mail=%s)' % student_data.email
        else:
            raise StudentUndefinedError()

        result = self.ldap_obj.search_s(self.scope, ldap.SCOPE_SUBTREE,
                                        query, self.default_filter)

        if not result:
            raise StudentNotFoundError()
        elif len(result) > 1:
            result = self.pick_best_result(result)

        entry = result[0][1]

        # Refresh the student description
        student_data.name=entry['displayName'][0].decode("utf8")
        student_data.email=entry['mail'][0].decode("utf8")
        student_data.gaspar=entry['uid'][0].decode("utf8")
        student_data.sciper=entry['uniqueIdentifier'][0].decode("utf8")

        return student_data
