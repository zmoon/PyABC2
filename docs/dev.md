# Instructions for developers

To contribute to this project, first fork it on GitHub and then clone your fork locally:
```
git clone https://github.com/<username>/PyABC2.git
```

Then set up a virtual env. For example:
```
python3 -m venv venv
source venv/bin/activate
```

Then install dependencies:
```
pip install flit
flit install --symlink
```
For Windows, use `--pth-file` instead of `--symlink`.

Then run tests to confirm that it works:
```
pytest -v -m "not slow"
```

Finally, there are several options for [installing `pre-commit`](https://pre-commit.com/#install).
Once it is installed, install the pre-commit hooks for this project:
```
pre-commit install
```

You can now make a branch on your fork, work on the code, push your branch to GitHub, and make a PR to the parent repo.
