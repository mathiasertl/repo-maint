# repo-maint

Private script to automatically update travis, requirements, etc in repos I maintain.

**NOTE:** This script is really just meant for private use. I don't intend to make this usable for everyone.

# Installation

Requires:
* [pyenv](https://github.com/pyenv/pyenv)
* [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

```
git clone git@github.com:mathiasertl/repo-maint.git
pyenv virtualenv 3.8.2 repo-maint
cd repo-maint
pyenv activate repo-maint
pip install -r requirements.txt
```

# Configuration

### requirements

Updates `requirements.txt` files using [pip-upgrader](https://github.com/simion/pip-upgrader). It will
automatically find:

* `requirements.txt`
* Files inside `requirements/`
* all files matching `requirements-*.txt` 
* included files

Possible configuration in `.repo-maint.yaml`:

```
requirements:
  # Completely ignore this check:
  #skip: true
  # Additional files to include:
  files:
    - some/subdir/custom-file-with-reqs.txt
  # Ignore some packages (case insensitive!)
  ignore:
    - Sphinx
```

### travis

Warns about outdated python versions in travis

Possible configuration in `.repo-maint.yaml`:

```
travis:
  python:
    # disable "nightly" as a travis version
    nightly: false
```
