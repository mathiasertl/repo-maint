#!/usr/bin/env python3
#
# This file is part of repo-maint (https://github.com/mathiasertl/repo-maint).
#
# repo-maint is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# repo-maint is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with repo-maint.  If not,
# see <http://www.gnu.org/licenses/>.

import importlib
import os
import pkgutil
import sys
from contextlib import contextmanager

from termcolor import colored

from repo_maint import checks


def get_checks(mod):
    Check = importlib.import_module('repo_maint.checks.base').Check

    checks = []
    for member in [getattr(mod, m) for m in dir(mod) if not m.startswith('_')]:
        # ignore members that are not classes or not defined here
        if not isinstance(member, type) or member.__module__ != mod.__name__:
            continue
        # append Check subclasses, but not Check itself
        if member != Check and issubclass(member, Check):
            checks.append(member)
    return list(sorted(checks, key=lambda c: c.order))


def get_check_modules():
    """Get all modules below repo_maint which have a class implementing repo_maint.checks.base.Check."""

    # Get Check class first

    for _modinfo, name, _ispkg in pkgutil.walk_packages(checks.__path__, checks.__name__ + '.'):
        mod = importlib.import_module(name)
        if get_checks(mod):
            yield mod


def red(msg, **kwargs):
    return colored(msg, 'red', **kwargs)


def green(msg, **kwargs):
    return colored(msg, 'green', **kwargs)


@contextmanager
def chdir(path):
    orig = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(orig)


@contextmanager
def hide_output():
    try:
        with open(os.devnull, 'w') as stream:
            sys.stdout = stream
            sys.stderr = stream
            yield
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
