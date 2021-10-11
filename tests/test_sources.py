import pytest

from pyabc2.parse import Tune
from pyabc2.sources import examples, load_example, load_example_abc, norbeck


@pytest.mark.parametrize("tune_name", examples)
def test_examples_load(tune_name):
    tune = load_example(tune_name)
    assert type(tune) is Tune


def test_bad_example_raises():
    with pytest.raises(ValueError):
        load_example_abc("asdf")


@pytest.mark.slow
def test_norbeck_load():
    # NOTE: downloads files if not already present

    tunes = norbeck.load()  # all
    jigs = norbeck.load("jigs")  # jigs only

    assert 0 < len(jigs) < len(tunes)

    assert type(jigs[0]) is Tune

    # Some diacritic tests
    assert jigs[512].title == "Buachaillín Buí, An"
    assert jigs[539].title == "30-årsjiggen"
    assert jigs[486].header["composer"] == "Annlaug Børsheim, Norway"

    with pytest.raises(ValueError):
        norbeck.load("asdf")
