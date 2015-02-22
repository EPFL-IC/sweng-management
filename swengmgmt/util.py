#!/usr/bin/env python
#
# Copyright 2012 EPFL. All rights reserved.


import contextlib
import os
import sys


"""Misc utilities."""


@contextlib.contextmanager
def hl_region(bold=False, color=None, fs=None):
    """Context manager for highlighting a region of screen."""

    fs = fs or sys.stdout

    if not os.isatty(fs.fileno()):
        yield
        return

    if bold:
        fs.write("\033[1m")
    if color:
        fs.write("\033[%dm" % (30 + color))

    yield

    fs.write("\033[0m")
    fs.flush()


def hl_str(s, bold=False, color=None, fs=None):
    fs = fs or sys.stdout

    if not os.isatty(fs.fileno()):
        return s

    return "".join(["\033[1m" if bold else "",
                    "\033[%dm" % (30 + color) if color else "",
                    s,
                    "\033[0m"])

def green(s):
    return hl_str(s, color=2)

def red(s):
    return hl_str(s, color=1)

def bold(s):
    return hl_str(s, bold=True)

def red_if_none(s):
    return red(bold("None")) if s is None else s

def red_green(s, r_value=None, g_value=None):
    if r_value is not None and s == r_value:
        return red(bold(s))
    elif g_value is not None and s == g_value:
        return green(bold(s))
    else:
        return s
