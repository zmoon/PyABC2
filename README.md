# PyABC2

[![CI workflow status](https://github.com/zmoon/PyABC2/actions/workflows/ci.yml/badge.svg)](https://github.com/zmoon/PyABC2/actions/workflows/ci.yml)
[![Test coverage](https://codecov.io/gh/zmoon/PyABC2/branch/main/graph/badge.svg)](https://app.codecov.io/gh/zmoon/PyABC2)
[![Version on PyPI](https://img.shields.io/pypi/v/pyabc2.svg)](https://pypi.org/project/pyabc2/)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

![image](https://user-images.githubusercontent.com/15079414/195207144-83df651a-6fe9-44b1-b7bc-e4aced14a2aa.png)

## Getting started

### Users

Install from PyPI:
```
pip install pyabc2
```
Then look at the [example notebooks](https://github.com/zmoon/PyABC2/tree/main/examples).

### Developers

To contribute to this project, first fork it on GitHub and then clone your fork locally:
```
git clone https://github.com/<username>/PyABC2.git
```

Then set up a virtual env. For example:
```
python3 -m venv venv
source venv/bin/activate
```

Then install dependencies and pre-commit hooks:
```
pip install flit
flit install --symlink
pre-commit install
```

Then run tests to confirm that it works:
```
pytest -v -m "not slow"
```

You can now make a branch on your fork, work on the code, push your branch to GitHub, and make a PR to the parent repo.

## Credits

Inspired in part by and some portions based on [PyABC](https://github.com/campagnola/pyabc) (`pyabc`; [MIT License](https://github.com/campagnola/pyabc/blob/master/LICENSE.txt)), hence "PyABC2" and the package name `pyabc2`. No relation to [this pyabc](https://github.com/icb-dcm/pyabc) that is on PyPI.
