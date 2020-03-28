#!/usr/bin/env python3

import glob
import os
import sys
from contextlib import contextmanager

import yaml
from pip_upgrader.packages_detector import PackagesDetector
from pip_upgrader.packages_status_detector import PackagesStatusDetector
from pip_upgrader.packages_upgrader import PackagesUpgrader
from pip_upgrader.requirements_detector import RequirementsDetector
from termcolor import colored

_binpath = os.path.normpath(os.path.realpath(__file__))
_bindir = os.path.dirname(_binpath)
_gitbase = os.path.expanduser('~/git/')

with open(os.path.join(_bindir, 'repo-maint.yaml')) as stream:
    config = yaml.load(stream, Loader=yaml.SafeLoader)


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


def red(msg, **kwargs):
    return colored(msg, 'red', **kwargs)


def green(msg, **kwargs):
    return colored(msg, 'green', **kwargs)


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


def check_requirements(repodir, local_config, reports):
    options = {'-p': ['all']}
    filenames = RequirementsDetector([]).get_filenames()
    filenames += list([f for f in local_config['requirements']['files'] if f not in filenames])
    filenames += glob.glob('requirements-*.txt')

    packages = PackagesDetector(filenames).get_packages()
    with hide_output():  # this outputs a lot to stdout :-(
        packages_status_map = PackagesStatusDetector(
            packages, use_default_index=True).detect_available_upgrades(options)

    selected_packages = {k: v for k, v in packages_status_map.items()
                         if v['upgrade_available'] and k not in local_config['requirements']['ignore']}

    options = {'--dry-run': False, '--skip-package-installation': True}
    with hide_output():  # this outputs a lot to stdout :-(
        upgraded_packages = PackagesUpgrader(selected_packages.values(), filenames, options).do_upgrade()

    reports += ['requirements: {name}: {current_version} -> {latest_version}'.format(**pkg)
                for pkg in upgraded_packages]


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

    # print reports for this repo
    if reports:
        print(red('[WARN]'))
        for report in reports:
            print('   * %s' % report)
    else:
        print(green('[OK]'))