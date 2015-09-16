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
import socket
import logging


class GithubAuthorizationError(Exception):
    pass

def two_factor_callback():
    try:
    # Python 2
        prompt = raw_input
    except NameError:
    # Python 3
        prompt = input

    code = ""
    while code == "":
        code = prompt("GitHub 2-Factor auth code: ")
    return code

class GithubAuthProvider(object):
    SCOPES = [ "repo", "delete_repo" ]

    def __init__(self, config, auth_config):
        self._config = config
        self._auth_config = auth_config
        self.token = None

    def authenticate(self, non_interactive=False):
        def attempt_auth(note):
            return github3.authorize(login=user_name,
                                     password=user_pwd,
                                     scopes=self.SCOPES,
                                     note_url=self._config["github_auth"]["url"],
                                     note=note,
                                     two_factor_callback=two_factor_callback)
        def code_exists(github_err):
            if github_err.code == 422:
                for error in github_err.errors:
                    if error.get('code') == 'already_exists':
                        return True
            return False

        self.token = self._auth_config.setdefault("github", {}).get("token")

        if not self.token:
            if non_interactive:
                raise GithubAuthorizationError("Interactive mode needed")

            user_name = raw_input("Enter Github login: ")
            user_pwd = getpass.getpass("Password:")
            note = self._config["github_auth"]["note"]
            try:
                auth = attempt_auth(note)
            except github3.GitHubError, ghe:
                if ghe.code == 422 and code_exists(ghe):
                    hostname = socket.gethostname()
                    logging.warning(
                        "GitHub: Authorization exists for url '{url}' and note '{note}'!\n\n\tExtending note with hostname '{host}'...".format(
                        url=self._config["github_auth"]["url"], note=note, host=hostname))
                    auth = attempt_auth("{note}, {host}".format(
                        note=note, host=hostname
                    ))
                else:
                    raise ghe
            self.token = auth.token
            logging.info("Got authorization token: %s" % self.token)

        self._auth_config["github"]["token"] = str(self.token)

    def getClient(self):
        return github3.login(token=self.token)
