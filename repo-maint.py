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
import subprocess

import yaml
from termcolor import colored

from repo_maint.requirements import check_requirements
from repo_maint.utils import chdir
from repo_maint.utils import green
from repo_maint.utils import red

_binpath = os.path.normpath(os.path.realpath(__file__))
_bindir = os.path.dirname(_binpath)
_gitbase = os.path.expanduser('~/git/')

with open(os.path.join(_bindir, 'repo-maint.yaml')) as stream:
    config = yaml.load(stream, Loader=yaml.SafeLoader)

parser = argparse.ArgumentParser(description="Make maintaining multiple repos at once easier.")
args = parser.parse_args()


def check_travis_config(repodir, local_config, reports):
    travis_config_path = os.path.join(repodir, '.travis.yml')
    if not os.path.exists(travis_config_path):
        return

    with open(travis_config_path) as stream:
        travis_config = yaml.load(stream, Loader=yaml.SafeLoader)

    if travis_config.get('language') == 'python':
        got = list(sorted(travis_config.get('python')))
        want = list(config['travis']['python']['versions'])
        if local_config['travis']['python']['nightly']:
            want.append('nightly')

        if got != want:
            reports.append('%s: python=%s, should be %s' % (
                os.path.basename(travis_config_path), got, want))

    return travis_config


def check_pyenv(repodir, local_config, reports):
    pyenv_config_path = os.path.join(repodir, '.python-version')
    if not os.path.exists(pyenv_config_path):
        return

    sp_kwargs = {'capture_output': True, 'check': True, 'encoding': 'utf-8'}  # reused a few times
    versions = subprocess.run(['pyenv', 'local'], **sp_kwargs).stdout.split()

    expected = sorted(config['pyenv']['versions'], reverse=True)
    if local_config['pyenv']['latest-versions']:
        expected = expected[:local_config['pyenv']['latest-versions']]
    if local_config['pyenv']['dev'] is True:
        expected.append(config['pyenv']['dev-version'])

    if versions != expected:
        subprocess.run(['pyenv', 'local'] + expected, **sp_kwargs)
        reports.append('pyenv versions updated to %s' % ', '.join(expected))

    basename = os.path.basename(repodir)
    venv_name = '%s/envs/%s' % (expected[0], basename)

    # get list of available venvs
    all_venvs = subprocess.run(['pyenv', 'versions', '--bare', '--skip-aliases'], **sp_kwargs).stdout.split()

    # delete any venvs with outdated versions
    for venv in [v for v in all_venvs if v.endswith(basename)]:
        if venv != venv_name:
            reports.append('pyenv: Delete %s' % venv)
            subprocess.run(['pyenv', 'uninstall', '--force', venv], **sp_kwargs)

    # install new venv if necessary
    if venv_name not in all_venvs:
        pyenv_env = dict({k: v for k, v in os.environ.items()
                          if not k.startswith('PYENV') and k != 'VIRTUAL_ENV'},
                         PYENV_VERSION=venv_name)

        subprocess.run(['pyenv', 'virtualenv', basename], **sp_kwargs)
        subprocess.run(['pyenv', 'exec', 'pip', 'install', '-U', 'pip', 'setuptools', 'wheel'],
                       env=pyenv_env, **sp_kwargs)

        reqs = [('-r', r) for r in local_config['pyenv']['requirements']]
        if reqs:
            reqs = [item for sublist in reqs for item in sublist]
            subprocess.run(['pyenv', 'exec', 'pip', 'install'] + reqs, env=pyenv_env, **sp_kwargs)
        reports.append('pyenv: Created new venv with Python %s' % expected[0])


for repo in config['repos']:
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
        ##############
        # travis.yml #
        ##############
        check_travis_config(repodir, local_config, reports)

        ####################
        # requirements.txt #
        ####################
        check_requirements(repodir, local_config, reports)

        ################
        # pyenv config #
        ################
        check_pyenv(repodir, local_config, reports)

    # print reports for this repo
    if reports:
        print(red('[WARN]'))
        for report in reports:
            print('   * %s' % report)
    else:
        print(green('[OK]'))
