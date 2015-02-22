#!/usr/bin/env python
#
# Copyright 2012 EPFL. All rights reserved.

"""EPFL student directory."""


import ldap


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

        entry = result[0][1]

        # Refresh the student description
        student_data.name=entry['displayName'][0].decode("utf8")
        student_data.email=entry['mail'][0].decode("utf8")
        student_data.gaspar=entry['uid'][0].decode("utf8")
        student_data.sciper=entry['uniqueIdentifier'][0].decode("utf8")

        return student_data