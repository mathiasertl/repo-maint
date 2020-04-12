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

import yaml

from .base import Check


class TravisCheck(Check):
    def check_repo(self, repodir, local_config, reports):
        travis_config_path = os.path.join(repodir, '.travis.yml')
        if not os.path.exists(travis_config_path):
            return
        config = local_config.get('travis', {})

        with open(travis_config_path) as stream:
            travis_config = yaml.load(stream, Loader=yaml.SafeLoader)

        if travis_config.get('language') == 'python':
            got = list(sorted(travis_config.get('python')))
            want = list(self.config['travis']['python']['versions'])
            if config.get('python', {}).get('nightly', True):
                want.append('nightly')

            if got != want:
                reports.append('%s: python=%s, should be %s' % (
                    os.path.basename(travis_config_path), got, want))

        return travis_config
