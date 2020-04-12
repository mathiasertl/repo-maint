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

import argparse
import os
import sys

import yaml
from termcolor import colored

from repo_maint.utils import chdir
from repo_maint.utils import get_check_modules
from repo_maint.utils import get_checks
from repo_maint.utils import green
from repo_maint.utils import red

_binpath = os.path.normpath(os.path.realpath(__file__))
_bindir = os.path.dirname(_binpath)
_gitbase = os.path.expanduser('~/git/')

with open(os.path.join(_bindir, 'repo-maint.yaml')) as stream:
    config = yaml.load(stream, Loader=yaml.SafeLoader)

parser = argparse.ArgumentParser(description="Make maintaining multiple repos at once easier.")
parser.add_argument('--list-modules', action='store_true', default=False,
                    help="List available modules and exit.")
parser.add_argument('--skip-module', action='append', default=[], metavar='MOD', dest='skip_modules',
                    help="Skip specific module check (use --list-modules to list available modules).")
parser.add_argument('-l', '--list-repos', action='store_true', default=False,
                    help="List all tested repositories and exit.")
parser.add_argument('repositories', nargs='*',
                    help="Only test listed repositories. If none given, check them all.")
args = parser.parse_args()

modules = list(get_check_modules())

if args.list_modules:
    for module in modules:
        print(module.__name__.rsplit('.', 1)[1])
    sys.exit()
if args.list_repos:
    for repo in config['repos']:
        print(repo)
    sys.exit()


modules = [m for m in modules if m.__name__.rsplit('.', 1)[1] not in args.skip_modules]

repos = config['repos']
if args.repositories:
    repos = args.repositories

for repo in repos:
    repodir = os.path.join(_gitbase, repo)

    if not os.path.exists(repodir):
        print('%s: Repo does not exist.' % repodir)
        continue

    # small safety check
    if not os.path.exists(os.path.join(repodir, '.git')):
        print('%s: No .git directory - not a git repo?' % repodir)
        continue

    reports = []

    local_config = {}
    local_config_path = os.path.join(repodir, '.repo-maint.yaml')
    if os.path.exists(local_config_path):
        with open(local_config_path) as stream:
            local_config = yaml.load(stream, Loader=yaml.SafeLoader)

    # set a few defaults in the config so its easier to handle
    local_config.setdefault('travis', {})
    local_config['travis'].setdefault('python', {})
    local_config['travis']['python'].setdefault('nightly', True)
    local_config.setdefault('requirements', {})
    local_config['requirements'].setdefault('files', [])
    local_config['requirements'].setdefault('ignore', {})
    local_config.setdefault('pyenv', {})
    local_config['pyenv'].setdefault('dev', False)
    local_config['pyenv'].setdefault('latest-versions', False)
    local_config['pyenv'].setdefault('requirements', [])
    print('%s... ' % colored(repodir, attrs=['bold']), end='', flush=True)

    with chdir(repodir):
        for module in modules:
            for check_cls in get_checks(module):
                check = check_cls(config)
                check.check_repo(repodir, local_config, reports)

    # print reports for this repo
    if reports:
        print(red('[WARN]'))
        for report in reports:
            print('   * %s' % report)
    else:
        print(green('[OK]'))
