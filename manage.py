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

"""Manage a Software Engineering class."""

__author__ = "stefan.bucur@epfl.ch (Stefan Bucur)"


import argparse
import logging
import os

from swengmgmt import commands


def main():
    # Parsing the program arguments
    parser = argparse.ArgumentParser(description="Student repository management.")
    commands.registerGlobalArguments(parser)
    commands.registerCommands(parser, commands.ALL_COMMANDS)

    args = parser.parse_args()

    if not os.path.isabs(args.config):
        args.config = os.path.join(os.path.dirname(__file__), args.config)
    if not os.path.isabs(args.auth):
        args.auth = os.path.join(os.path.dirname(__file__), args.auth)

    # Configure logging
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='-- [%(asctime)s] %(message)s')
    if not args.debug:
        requests_logger = logging.getLogger("requests")
        requests_logger.setLevel(logging.WARNING)
        github3_logger = logging.getLogger("github3")
        github3_logger.setLevel(logging.WARNING)

    try:
        args.command.execute(args)
    finally:
        args.command.finalize()


if __name__ == "__main__":
    main()
