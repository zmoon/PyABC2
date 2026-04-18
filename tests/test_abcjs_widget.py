import pytest
import traitlets

from pyabc2.abcjs.widget import ABCJSWidget


def test_chord_grid_validation():
    with pytest.raises(traitlets.TraitError, match="chord_grid must be one of"):
        _ = ABCJSWidget(chord_grid="asdf")

    w = ABCJSWidget()
    assert w.chord_grid is None
    with pytest.raises(traitlets.TraitError, match="chord_grid must be one of"):
        w.chord_grid = "asdf"
    w.chord_grid = "withMusic"
    assert w.chord_grid == "withMusic"
    w.chord_grid = None
    assert w.chord_grid is None
