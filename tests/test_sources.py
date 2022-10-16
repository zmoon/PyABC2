import pytest

from pyabc2 import Key
from pyabc2.parse import Tune
from pyabc2.sources import examples, load_example, load_example_abc, load_url, norbeck, the_session


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
    assert all(t in tunes for t in jigs)
    assert set(jigs) < set(tunes)

    assert type(jigs[0]) is Tune

    assert len(set(jigs)) == len(jigs)

    # Some diacritic tests
    assert jigs[512].title == "Buachaillín Buí, An"
    assert jigs[539].title == "30-årsjiggen"
    assert jigs[486].header["composer"] == "Annlaug Børsheim, Norway"

    with pytest.raises(ValueError):
        norbeck.load("asdf")


@pytest.mark.parametrize(
    "url,title,key,type",
    [
        ("https://thesession.org/tunes/182", "The Silver Spear", "D", "reel"),
        ("https://thesession.org/tunes/182#setting22284", "The Silver Spear", "C", "reel"),
    ],
)
def test_the_session_load_url(url, title, key, type):
    tune = the_session.load_url(url)
    assert tune.title == title
    assert tune.key == Key(key)
    assert tune.type == type


def test_the_session_url_check():
    with pytest.raises(AssertionError):
        the_session.load_url("https://www.google.com")


def test_the_session_load_archive():
    # NOTE: downloads file if not already present

    _ = the_session.load(n=5)  # TODO: all? (depending on time)


def test_load_url():
    tune = load_url("https://thesession.org/tunes/10000")
    assert tune.title == "Brian Quinn's"

    tune = load_url("https://norbeck.nu/abc/display.asp?rhythm=slip+jig&ref=106")
    assert tune.title == "For The Love Of Music"

    with pytest.raises(NotImplementedError):
        _ = load_url("https://www.google.com")
