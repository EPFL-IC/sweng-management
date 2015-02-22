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

"""Github support."""


import getpass
import github3
import logging


class GithubAuthorizationError(Exception):
    pass

class GithubAuthProvider(object):
    SCOPES = [ "repo", "delete_repo" ]

    def __init__(self, config, auth_config):
        self._config = config
        self._auth_config = auth_config
        self.token = None

    def authenticate(self, non_interactive=False):
        self.token = self._auth_config.setdefault("github", {}).get("token")

        if not self.token:
            if non_interactive:
                raise GithubAuthorizationError("Interactive mode needed")

            user_name = raw_input("Enter Github login: ")
            user_pwd = getpass.getpass("Password:")

            auth = github3.authorize(user_name, user_pwd,
                                     self.SCOPES,
                                     self._config["github_auth"]["note"],
                                     self._config["github_auth"]["url"])
            self.token = auth.token
            logging.info("Got authorization token: %s" % self.token)

        self._auth_config["github"]["token"] = str(self.token)

    def getClient(self):
        return github3.login(token=self.token)
