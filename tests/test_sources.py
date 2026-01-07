import re
import warnings

import pytest

from pyabc2 import Key
from pyabc2.parse import Tune
from pyabc2.sources import (
    eskin,
    examples,
    load_example,
    load_example_abc,
    load_url,
    norbeck,
    the_session,
)

NORBECK_IRISH_COUNT = 2733


@pytest.mark.parametrize("tune_name", examples)
def test_examples_load(tune_name):
    tune = load_example(tune_name)
    assert type(tune) is Tune


def test_bad_example_raises():
    with pytest.raises(ValueError):
        load_example_abc("asdf")


def test_example_random():
    tune = load_example()
    assert type(tune) is Tune


def test_norbeck_tune_type_file_prefix():
    norbeck._maybe_download()
    all_fps = list(norbeck.SAVE_TO.glob("*.abc"))
    fps_type = {}
    for typ in norbeck._TYPE_PREFIX:
        fps_type[typ] = norbeck._get_paths_type(typ)
        assert len(fps_type[typ]) > 0

    all_fps_type = [p for lst in fps_type.values() for p in lst]
    all_fps_type_set = set(all_fps_type)
    assert len(all_fps_type) == len(all_fps_type_set)
    assert set(all_fps) == all_fps_type_set


def test_norbeck_x_unique():
    # X value should be unique within tune type
    norbeck._maybe_download()
    xs = []
    for typ in norbeck._TYPE_PREFIX:
        for p in norbeck._get_paths_type(typ):
            with open(p, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("X:"):
                        x = int(line[2:])
                        xs.append((typ, x))

    assert len(set(xs)) == len(xs), "X unique"


def test_norbeck_x_vals():
    # Make sure they match with what file says
    norbeck._maybe_download()
    ntot = 0
    for p in norbeck.SAVE_TO.glob("*.abc"):
        with open(p, "r") as f:
            s = f.read()
            lines = s.splitlines()
            m = re.fullmatch(
                r"This file contains ([0-9]{1,3}) .* \(#([0-9]+)\s*-\s*#([0-9]+)\).", lines[0]
            )
            assert m is not None
            n, a, b = [int(x) for x in m.groups()]
            assert n >= 1
            assert b - a + 1 == n
            assert s.count("X:") == n
            xs = re.findall(r"^X:([0-9]+)\s*$", s, flags=re.MULTILINE)
            nums = [int(m) for m in xs]
            assert len(nums) == n
            assert set(range(a, b + 1)) == set(nums)
            ntot += n

    assert ntot == NORBECK_IRISH_COUNT


@pytest.mark.slow
def test_norbeck_load():
    # NOTE: downloads files if not already present

    tunes = norbeck.load()  # all
    jigs = norbeck.load("jigs")  # jigs only
    hps = norbeck.load("hornpipes")

    # One of the expected failures (has chords)
    assert "Pride of Petravore, The" not in set([t.title for t in tunes])
    assert "Pride of Petravore, The" not in set([t.title for t in hps])

    n_exp_fail = sum(len(lst) for d in norbeck._EXPECTED_FAILURES.values() for lst in d.values())
    assert len(tunes) == NORBECK_IRISH_COUNT - n_exp_fail

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
    if "#" in url:  # Currently always gets set to a specific setting
        assert tune.url == url
    if "#" not in url:  # First setting
        assert tune.header["reference number"] == "1"


def test_the_session_url_check():
    with pytest.raises(AssertionError):
        the_session.load_url("https://www.google.com")


def test_the_session_load_archive():
    # NOTE: downloads file if not already present

    _ = the_session.load(n=5)  # TODO: all? (depending on time)

    with pytest.warns(UserWarning, match=r"The Session tune\(s\) failed to load"):
        tunes1 = the_session.load(n=200)
        tunes2 = the_session.load(n=200, num_workers=2)
    assert tunes1 == tunes2


def test_the_session_download_invalid():
    with pytest.raises(ValueError):
        _ = the_session.download("asdf")


@pytest.mark.slow
@pytest.mark.parametrize(
    "which", ["aliases", "events", "recordings", "sessions", "sets", "tune_popularity", "tunes"]
)
def test_the_session_load_meta(which):
    import numpy as np
    import pandas as pd
    from pandas.testing import assert_frame_equal

    df1 = the_session.load_meta(which)
    df1_csv = the_session.load_meta(which, format="csv")
    df2 = the_session.load_meta(which, downcast_ints=True)
    df3 = the_session.load_meta(which, convert_dtypes=True)

    try:
        assert df1.equals(df1_csv)
    except AssertionError:
        unequal = ~(df1 == df1_csv)
        df1_ = df1[unequal].dropna(axis="index", how="all").dropna(axis="columns", how="all")
        df1_csv_ = (
            df1_csv[unequal].dropna(axis="index", how="all").dropna(axis="columns", how="all")
        )
        cmp = pd.concat([df1_, df1_csv_.rename(columns=lambda c: f"{c}_csv")], axis="columns")
        warnings.warn(f"CSV and JSON for {which} have differences:\n{cmp}")

    assert_frame_equal(df1, df2, check_dtype=False)
    assert not (df2.dtypes == df1.dtypes).all()
    assert not (df3.dtypes == df1.dtypes).all()
    if "latitude" in df1:
        for df in [df1, df1_csv, df2]:
            assert df.latitude.dtype == np.float64
            assert df.longitude.dtype == np.float64
        # in df3, `pd.Float64Dtype()`


def test_the_session_load_meta_invalid():
    with pytest.raises(ValueError):
        _ = the_session.load_meta("asdf")

    with pytest.raises(ValueError):
        _ = the_session.load_meta("sessions", format="asdf")


def test_the_session_load_meta_doc_consistency():
    s_options = ", ".join(repr(x) for x in sorted(the_session._META_ALLOWED))
    expected_line = f"which : {{{s_options}}}"
    assert the_session.load_meta.__doc__ is not None
    assert expected_line in the_session.load_meta.__doc__


def test_int_downcast():
    import numpy as np
    import pandas as pd

    for x, expected_dtype, expected_dtype_ext in [
        # short short (8)
        ([int(1e2)], np.uint8, pd.UInt8Dtype()),
        ([int(1e2), -1], np.int8, pd.Int8Dtype()),
        # short (16)
        ([int(1e4)], np.uint16, pd.UInt16Dtype()),
        ([int(1e4), -1], np.int16, pd.Int16Dtype()),
        # long (32)
        ([int(1e9)], np.uint32, pd.UInt32Dtype()),
        ([int(1e9), -1], np.int32, pd.Int32Dtype()),
        # long long (64)
        ([int(1e18)], np.uint64, pd.UInt64Dtype()),
        ([int(1e18), -1], np.int64, pd.Int64Dtype()),
    ]:
        s = pd.Series(x)
        assert s.dtype == np.int64

        s2 = s.astype(the_session._choose_int_type(s))
        assert s2.dtype == expected_dtype

        s3 = s.astype(the_session._choose_int_type(s, ext=True))
        assert s3.dtype == expected_dtype_ext


def test_load_url_the_session():
    tune = load_url("https://thesession.org/tunes/10000")
    assert tune.title == "Brian Quinn's"


def test_load_url_norbeck():
    import requests

    url = "https://norbeck.nu/abc/display.asp?rhythm=slip+jig&ref=106"
    try:
        tune = load_url(url)
    except requests.exceptions.ReadTimeout as e:
        warnings.warn(f"reading Norbeck URL {url} timed out. ({e})")
    else:
        assert tune.title == "For The Love Of Music"


def test_load_url_invalid_domain():
    with pytest.raises(NotImplementedError):
        _ = load_url("https://www.google.com")


@pytest.mark.parametrize("key", eskin._TUNEBOOK_KEY_TO_URL)
def test_eskin_tunebook_url_exist(key):
    import requests

    url = eskin._TUNEBOOK_KEY_TO_URL[key]
    r = requests.head(url, timeout=5)
    r.raise_for_status()
    # Bad URLs seem to just redirect to his homepage,
    # so we need to check the final URL
    # TODO: maybe move this to the module
    if (
        r.status_code == 302
        and r.headers.get("Location", "").rstrip("/") == "https://michaeleskin.com"
    ):
        raise ValueError(f"{key!r} URL {url} redirects to homepage")


def test_eskin_tunebook_url_current():
    import requests

    url = "https://michaeleskin.com/tunebooks.html"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    if (
        r.status_code == 302
        and r.headers.get("Location", "").rstrip("/") == "https://michaeleskin.com"
    ):
        raise ValueError(f"URL {url} redirects to homepage")
    html = r.text

    old_keys = {
        "cce_san_diego_jan2025",
        "hardy_2024",
    }
    for key, tb_url in eskin._TUNEBOOK_KEY_TO_URL.items():
        m = re.search(rf'href=["\']({tb_url})["\']', html)
        if key in old_keys:
            assert m is None
        else:
            if m is None:
                raise ValueError(f"Could not find link for tunebook {key!r} in tunebooks page.")


@pytest.mark.parametrize("key", eskin._TUNEBOOK_KEY_TO_URL)
def test_eskin_tunebook_data_load(key):
    data = eskin.load_meta(key)

    tune_type_keys = {
        "airs_songs",
        "hornpipes",
        "jigs",
        "long_dances",
        "marches",
        "misc_tunes",
        "ocarolan",
        "polkas",
        "reels",
        "scotchreels",
        "slides",
        "slipjigs",
        "strathspeys",
        "waltzes",
    }

    assert data.keys() <= tune_type_keys or list(data) == ["tunes"]


def test_eskin_abc_url_creation():
    import requests

    abc = load_example_abc("For the Love of Music")

    url = eskin.abc_to_abctools_url(abc)
    r = requests.head(url, timeout=5)
    r.raise_for_status()
    if (
        r.status_code == 302
        and r.headers.get("Location", "").rstrip("/") == "https://michaeleskin.com"
    ):
        raise ValueError(f"URL {url} redirects to homepage")
