"""
Test top-level
"""
from importlib.metadata import metadata  # type: ignore[import]

pyabc2_metadata = metadata("pyabc2")

import pyabc2


def test_version():
    assert pyabc2.__version__ == pyabc2_metadata["version"]


def test_short_description_consistency():
    module_descrip = pyabc2.__doc__.strip().split("\n")[0]

    assert module_descrip == pyabc2_metadata["summary"]
