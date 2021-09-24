"""
Test top-level
"""
import pyabc2


def test_version():
    # pyproject.toml as the source of truth
    # (controlled by `poetry version ...`)
    with open("pyproject.toml", "r") as f:
        line = f.readlines()[2]

    pyproject_version = line.partition("=")[-1].strip(' \n"')

    assert pyabc2.__version__ == pyproject_version


def test_short_description_consistency():
    # pyproject.toml as the source of truth
    with open("pyproject.toml", "r") as f:
        line = f.readlines()[3]

    pyproject_descrip = line.partition("=")[-1].strip(' \n"')
    module_descrip = pyabc2.__doc__.strip().split("\n")[0]

    assert module_descrip == pyproject_descrip
