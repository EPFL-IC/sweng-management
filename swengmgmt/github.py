#!/usr/bin/env python
#
# Copyright 2012 EPFL. All rights reserved.

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
