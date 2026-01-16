# Instructions for developers

To contribute to this project, first fork it on GitHub and then clone your fork locally
(replacing `<username>` with your GitHub username):
```none
git clone https://github.com/<username>/PyABC2.git
```

Then set up a virtual environment and install dependencies. For example:

````{tab} Linux/macOS
```sh
python -m venv venv
source venv/bin/activate
```
```sh
pip install flit
flit install --symlink
```
````

````{tab} Windows
```pwsh
python -m venv venv
venv\Scripts\activate
```
```sh
pip install flit
flit install --pth-file
```
````

Then run tests to confirm that it works:
```sh
pytest -v -m "not slow"
```

Finally, there are several options for [installing `pre-commit`](https://pre-commit.com/#install).
Once it is installed, install the pre-commit hooks for this project:
```sh
pre-commit install
```

You can now make a branch on your fork, work on the code, push your branch to GitHub, and make a PR to the parent repo.

## Widget

Enable hot reloading by setting environment variable `ANYWIDGET_HMR` to `1`
before starting Jupyter Lab.

````{tab} Bash
```bash
export ANYWIDGET_HMR=1
```
````
````{tab} PowerShell
```powershell
$env:ANYWIDGET_HMR = "1"
```
````
