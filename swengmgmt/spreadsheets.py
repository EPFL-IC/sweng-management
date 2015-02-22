#!/usr/bin/env python
#
# Copyright 2012 EPFL. All rights reserved.

"""Google Spreadsheets manipulation."""


import logging

import gdata.gauth
import gdata.spreadsheets.client

from swengmgmt import epfl


DEFAULT_STUDENTS_WORKSHEET = "Students"
DEFAULT_TEAMS_WORKSHEET = "Teams"


class AuthorizationFailedError(Exception):
    pass


class GDataOAuthProvider(object):
    # Offline access
    CLIENT_REDIRECT = "urn:ietf:wg:oauth:2.0:oob"

    # Only need r/w access to the spreadsheets
    CLIENT_SCOPES = [ "https://spreadsheets.google.com/feeds" ]
    CLIENT_USER_AGENT = "SwEng"


    def __init__(self, config, auth_config):
        self._config = config
        self._auth_config = auth_config
        self.token = None

    def authenticate(self, non_interactive=False):
        token_blob = self._auth_config.setdefault("google", {}).get("token")
        if token_blob:
            self.token = gdata.gauth.token_from_blob(token_blob)

        if not self.token or self.token.invalid:
            if non_interactive:
                raise AuthorizationFailedError("Interactive mode needed")

            self.token = gdata.gauth.OAuth2Token(
                client_id=self._config["google_auth"]["client_id"],
                client_secret=self._config["google_auth"]["client_secret"],
                scope=" ".join(self.CLIENT_SCOPES),
                user_agent=self.CLIENT_USER_AGENT)

            auth_url = self.token.generate_authorize_url(
                redirect_uri=self.CLIENT_REDIRECT)
            print "Authorizing Spreadsheets access. Follow this link ",
            print "in your web browser:"
            print
            print auth_url
            print

            auth_code = raw_input("Enter authorization code: ")
            self.token.get_access_token(auth_code)

        if self.token.invalid:
            raise AuthorizationFailedError("Could not authorize the app")

        self._auth_config["google"]["token"] = str(gdata.gauth.token_to_blob(self.token))

    def getClient(self):
        client = gdata.spreadsheets.client.SpreadsheetsClient()
        return self.token.authorize(client)


class DataSpreadsheet(object):
    """Interface to a worksheet in a Google spreadsheet."""

    def __init__(self, client, ssheet_title, wsheet_name):
        self._ssheet_title = ssheet_title
        self._wsheet_name = wsheet_name
        self._client = client

        self.ssheet_key = None
        self.wsheet_id = None

    def _fetchSpreadsheet(self):
        if self.ssheet_key and self.wsheet_id:
            return

        ssheet_q = gdata.spreadsheets.client.SpreadsheetQuery(
            title=self._ssheet_title,
            title_exact=True)
        ssheet_feed = self._client.get_spreadsheets(q=ssheet_q)
        self.ssheet_key = ssheet_feed.entry[0].get_spreadsheet_key()

        wsheet_q = gdata.spreadsheets.client.WorksheetQuery(
            title=self._wsheet_name,
            title_exact=True)
        wsheet_feed = self._client.get_worksheets(self.ssheet_key, q=wsheet_q)
        self.wsheet_id = wsheet_feed.entry[0].get_worksheet_id()


class SwEngStudentSpreadsheet(DataSpreadsheet):
    """Interface to a SwEng students worksheet."""

    def __init__(self, client, ssheet_title, wsheet_name=None):
        wsheet_name = wsheet_name or DEFAULT_STUDENTS_WORKSHEET

        super(SwEngStudentSpreadsheet, self).__init__(client,
                                                      ssheet_title,
                                                      wsheet_name)

    def repair(self, ldap_object):
        self._fetchSpreadsheet()

        list_feed = self._client.get_list_feed(self.ssheet_key, self.wsheet_id)
        for entry in list_feed.entry:
            student = epfl.EPFLStudentData(
                name=entry.get_value("name"),
                email=entry.get_value("e-mail"),
                gaspar=entry.get_value("gaspar"),
                sciper=entry.get_value("sciper"))

            try:
                ldap_object.lookup(student)
            except epfl.StudentNotFoundError:
                logging.warning("%s not found. Skipping." % student)
                continue

            entry.set_value("name", student.name)
            entry.set_value("e-mail", student.email)
            entry.set_value("gaspar", student.gaspar)
            entry.set_value("sciper", student.sciper)
            self._client.update(entry)

            logging.info("Updated %s" % student)

    def getStudentList(self, student_factory):
        self._fetchSpreadsheet()

        result = []
        list_feed = self._client.get_list_feed(self.ssheet_key, self.wsheet_id)
        for entry in list_feed.entry:
            student = student_factory(
                name=(entry.get_value("name") or "").strip(),
                email=(entry.get_value("e-mail") or "").strip(),
                gaspar=(entry.get_value("gaspar") or "").strip(),
                sciper=(entry.get_value("sciper") or "").strip(),
                team_name=(entry.get_value("team") or "").strip(),
                github_id=(entry.get_value("githubid") or "").strip())

            result.append(student)

        return result


class SwEngTeamSpreadsheet(DataSpreadsheet):
    """Interface to a SwEng teams worksheet."""

    def __init__(self, client, spreadsheet_title, wsheet_name=None):
        wsheet_name = wsheet_name or DEFAULT_TEAMS_WORKSHEET

        super(SwEngTeamSpreadsheet, self).__init__(client,
                                                   spreadsheet_title,
                                                   wsheet_name)

    def getTeamList(self, team_factory):
        self._fetchSpreadsheet()

        result = []
        list_feed = self._client.get_list_feed(self.ssheet_key, self.wsheet_id)
        for entry in list_feed.entry:
            team = team_factory(
                name=entry.get_value("team").strip(),
                github_slug=entry.get_value("githubslug").strip())
            result.append(team)

        return result
