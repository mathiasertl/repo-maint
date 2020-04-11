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
