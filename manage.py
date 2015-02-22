#!/usr/bin/env python
#
# Copyright 2012 EPFL. All rights reserved.

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
