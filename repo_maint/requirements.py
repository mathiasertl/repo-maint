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

import glob

from pip_upgrader.packages_detector import PackagesDetector
from pip_upgrader.packages_status_detector import PackagesStatusDetector
from pip_upgrader.packages_upgrader import PackagesUpgrader
from pip_upgrader.requirements_detector import RequirementsDetector

from .utils import hide_output


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
