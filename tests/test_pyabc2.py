"""
Test top-level
"""
try:
    from importlib.metadata import metadata
except ModuleNotFoundError:
    im_avail = False
else:
    im_avail = True
    pyabc2_metadata = metadata("pyabc2")

import pytest

import pyabc2


@pytest.mark.skipif(not im_avail, reason="no importlib.metadata")
def test_version():
    assert pyabc2.__version__ == pyabc2_metadata["version"]


@pytest.mark.skipif(not im_avail, reason="no importlib.metadata")
def test_short_description_consistency():
    module_descrip = pyabc2.__doc__.strip().split("\n")[0]

    assert module_descrip == pyabc2_metadata["summary"]
