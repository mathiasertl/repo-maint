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

import os
import subprocess

from .base import Check


class PyenvCheck(Check):
    def check_repo(self, repodir, local_config, reports):
        pyenv_config_path = os.path.join(repodir, '.python-version')
        if not os.path.exists(pyenv_config_path) or local_config['pyenv'].get('skip', False):
            return

        sp_kwargs = {'capture_output': True, 'check': True, 'encoding': 'utf-8'}  # reused a few times
        versions = subprocess.run(['pyenv', 'local'], **sp_kwargs).stdout.split()

        expected = sorted(self.config['pyenv']['versions'], reverse=True)
        if local_config['pyenv']['latest-versions']:
            expected = expected[:local_config['pyenv']['latest-versions']]
        if local_config['pyenv']['dev'] is True:
            expected.append(self.config['pyenv']['dev-version'])

        basename = os.path.basename(repodir)
        venv_name = '%s/envs/%s' % (expected[0], basename)  # this is

        # Add <newest-python>/envs/<dirname> on top of .python-versions, if requested
        if local_config['pyenv'].get('virtualenv') is True:
            expected.insert(0, venv_name)

        if versions != expected:
            subprocess.run(['pyenv', 'local'] + expected, **sp_kwargs)
            reports.append('pyenv versions updated to %s' % ', '.join(expected))

        # get list of available venvs
        all_venvs = subprocess.run(
            ['pyenv', 'versions', '--bare', '--skip-aliases'], **sp_kwargs).stdout.split()

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
