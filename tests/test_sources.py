import re
import warnings

import pytest

from pyabc2 import Key
from pyabc2.parse import Tune
from pyabc2.sources import (
    bill_black,
    bill_black_tunefolders,
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
            with open(p) as f:
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
        with open(p) as f:
            s = f.read()
            lines = s.splitlines()
            m = re.fullmatch(
                r"This file contains ([0-9]{1,3}) .* \(#([0-9]+)\s*-\s*#([0-9]+)\).", lines[0]
            )
            assert m is not None
            n, a, b = (int(x) for x in m.groups())
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
    assert "Pride of Petravore, The" not in {t.title for t in tunes}
    assert "Pride of Petravore, The" not in {t.title for t in hps}

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


def test_the_session_load_archive_threaded():
    # NOTE: downloads file if not already present
    with pytest.warns(UserWarning, match=r"The Session tune\(s\) failed to load"):
        tunes1 = the_session.load(n=200)
    with pytest.warns(UserWarning, match=r"The Session tune\(s\) failed to load"):
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


@pytest.mark.parametrize("netloc", sorted(the_session._URL_NETLOCS))
def test_load_url_the_session(netloc):
    tune = load_url(f"https://{netloc}/tunes/10000")
    assert tune.title == "Brian Quinn's"


@pytest.mark.parametrize("netloc", sorted(norbeck._URL_NETLOCS))
def test_load_url_norbeck(netloc):
    import requests

    url = f"https://{netloc}/abc/display.asp?rhythm=slip+jig&ref=106"
    try:
        tune = load_url(url)
    except requests.exceptions.ReadTimeout as e:
        warnings.warn(f"reading Norbeck URL {url} timed out. ({e})")
    else:
        assert tune.title == "For The Love Of Music"


@pytest.mark.parametrize("netloc", sorted(eskin._URL_NETLOCS))
def test_load_url_eskin(netloc):
    url = f"https://{netloc}/abctools/abctools.html?lzw=BoLgUAKiBiD2BOACCALApogMrAbhg8gGaICyArgM4CWAxmAEogUA2VADogFZUDmYAwiExUAXon4BDePFjNmYEiACcAegAcYTCACM6sAGkQAcTBGAogBFEFs0cQBBIwCFEAHwdG7zgCaI0333dzKxs7Rxo3RCc0DCd7F3MzRBBXMB5-PxVCFR4EpxUaFUDEdN80HgAjRAkAJmJ3Uszs3Id8wuL-F28nMKdAtIy0LJy8gqLIxvKq2olIipimnIxankjOxG7e+zdUoA"
    tune = load_url(url)
    assert tune.title == "For The Love Of Music"


def test_load_url_invalid_domain():
    with pytest.raises(NotImplementedError):
        _ = load_url("https://www.google.com")


def test_eskin_tunebook_bad_url_redirects():
    import requests

    # Bad URL (2025 -> 3025)
    # Redirects to the home page.
    # Nothing in `r.history`. `allow_redirects=False` has no impact.
    url = "https://michaeleskin.com/cce_sd/cce_san_diego_tunes_10nov3025.html"
    r = requests.head(url, timeout=5)
    r.raise_for_status()

    assert r.status_code == 302
    assert r.headers.get("Location", "").rstrip("/") == "https://michaeleskin.com"
    assert r.history == []
    assert r.is_redirect


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
    df = eskin.load_meta(key)

    tune_group_keys = {
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

    if key in {"kss"}:
        assert set(df.group.unique()) <= tune_group_keys
    else:
        assert df.group.unique().tolist() == ["tunes"]


def test_eskin_abc_url_parsing():
    # From https://michaeleskin.com/cce_sd/cce_san_diego_tunes_10nov2025.html
    url = "https://michaeleskin.com/abctools/abctools.html?lzw=BoLgjAUApFAuCWsA2BTAZgewHawAQAUBDJQhLDXMADmigGcBXAIwWXWzyJLIrAGZa8LJkw4CxUkN4CYAB0IAnWHVGcJPSjLgoAtrIyrx3KZtqwUAD1iGuk8qYAqIBwAsUuAIJMmKAJ64IABlwAHoaAFkQABYQqIgARRAAJliAXgBOAAYIACUQHJQUJGg6AHchAHNcTIA6SABpEABxaEImAGMAKzoAfToMBiwAE0M0UiYMX1pwgEkAERncWQUMCoVCHWrp+cWmQjo6ZdWtmFmF3HaXDAUho6rs053cPYOANwwkXAA2OMfzy+uQ3enx+rSGQx6xCQPVkJF8e3aAGsekghIi6BAAEQeHSYzx8XAAIU8SVwTQAorgAD6eDxNDy4TFNPGE8HEmnY3G0jzEunkgBi1MZzLJTXpRLZ1KxOLxHlJPJJZMpNI8dIZTJZko5MsVCr5go5IrF4tZQyqVKp0q5KAqttwhFJeyFGtwFTaVUIFRQQ2dOptdodrsIzuZTDdaFd7iGpMtnLx-o9FTDIcxnuTnu9vutto9pLdKbDhAjXqG7IAukA&format=noten&ssp=10&name=The_Abbey&play=1"

    # default: explicit prefixes
    abc = eskin.abctools_url_to_abc(url)

    # any %
    abc_rm_any_pct = eskin.abctools_url_to_abc(url, remove_prefs="%")

    # no remove
    abc_no_rm = eskin.abctools_url_to_abc(url, remove_prefs=False)

    assert abc == abc_rm_any_pct
    assert sum(line.startswith("%") for line in abc_no_rm.splitlines()) > 0
    assert sum(line.startswith(r"%%") for line in abc_no_rm.splitlines()) > 0


def test_eskin_abc_url_missing_param():
    url = "https://michaeleskin.com/abctools/abctools.html?"
    with pytest.raises(ValueError, match="URL does not contain required 'lzw' parameter"):
        _ = eskin.abctools_url_to_abc(url)


def test_eskin_abc_url_bad_param():
    url = "https://michaeleskin.com/abctools/abctools.html?lzw=hi"
    with pytest.raises(RuntimeError, match="Failed to decompress LZString data"):
        _ = eskin.abctools_url_to_abc(url)


def test_eskin_abc_url_bad(caplog):
    url = "https://michaeleski.com/deftools/abctools.html?lzw=BoLgjAUApFAuCWsA2BTAZgewHawAQAUBDJQhLDXMADmigGcBXAIwWXWzyJLIrAGZa8LJkw4CxUkN4CYAB0IAnWHVGcJPSjLgoAtrIyrx3KZtqwUAD1iGuk8qYAqIBwAsUuAIJMmKAJ64IABlwAHoaAFkQABYQqIgARRAAJliAXgBOAAYIACUQHJQUJGg6AHchAHNcTIA6SABpEABxaEImAGMAKzoAfToMBiwAE0M0UiYMX1pwgEkAERncWQUMCoVCHWrp+cWmQjo6ZdWtmFmF3HaXDAUho6rs053cPYOANwwkXAA2OMfzy+uQ3enx+rSGQx6xCQPVkJF8e3aAGsekghIi6BAAEQeHSYzx8XAAIU8SVwTQAorgAD6eDxNDy4TFNPGE8HEmnY3G0jzEunkgBi1MZzLJTXpRLZ1KxOLxHlJPJJZMpNI8dIZTJZko5MsVCr5go5IrF4tZQyqVKp0q5KAqttwhFJeyFGtwFTaVUIFRQQ2dOptdodrsIzuZTDdaFd7iGpMtnLx-o9FTDIcxnuTnu9vutto9pLdKbDhAjXqG7IAukA&format=noten&ssp=10&name=The_Abbey&play=1"
    with caplog.at_level("DEBUG"):
        _ = eskin.abctools_url_to_abc(url)

    assert caplog.messages == [
        "Unexpected Eskin URL netloc: michaeleski.com",
        "Unexpected Eskin URL path: /deftools/abctools.html",
    ]


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


def test_eskin_invalid_tunebook_key():
    with pytest.raises(ValueError, match="Unknown Eskin tunebook key: 'asdf'"):
        _ = eskin.get_tunebook_info("asdf")


def test_bill_black_no_https():
    # If the site does get HTTPS, we'd like to know
    import requests

    url = "http://www.capeirish.com/ittl/tunefolders/"
    url_https = url.replace("http://", "https://")

    r = requests.head(url, headers={"User-Agent": "pyabc2"}, timeout=5)
    r.raise_for_status()

    with pytest.raises(requests.exceptions.SSLError):
        r = requests.head(url_https, headers={"User-Agent": "pyabc2"}, timeout=5)
        r.raise_for_status()


@pytest.mark.parametrize("key", list(bill_black_tunefolders._KEY_TO_COLLECTION))
def test_bill_black_tunefolders(key):
    import requests

    col = bill_black_tunefolders.get_collection(key)
    if int(col.folder) in {14, 18, 21, 25, 49}:
        # 14, 18, 25 -- These only have .txt now, not .rtf
        # 21 -- some subfolder names don't match the file names
        # 49 -- has subsubfolders
        with pytest.raises(requests.exceptions.HTTPError) as e:
            lst = bill_black_tunefolders.load_meta(key)
        assert e.value.response.status_code == 404
        return
    else:
        lst = bill_black_tunefolders.load_meta(key)

    assert len(lst) > 0


def test_bill_black_tunefolders_invalid_key():
    with pytest.raises(ValueError, match="Unknown collection key: 'asdf'"):
        _ = bill_black_tunefolders.get_collection("asdf")


def test_bill_black_text_fns():
    import requests

    url = "http://www.capeirish.com/ittl/alltunes/text/"
    r = requests.get(url, headers={"User-Agent": "pyabc2"}, timeout=5)
    r.raise_for_status()

    fns_web = sorted(re.findall(r'href=["\']([a-z0-9\-]+\.txt)["\']', r.text))
    if "s-tunes-1.txt" in fns_web:
        # We're using s-tunes-2, not both
        fns_web.remove("s-tunes-1.txt")

    assert bill_black.TXT_FNS == fns_web


def test_bill_black_load():
    lst = bill_black.load_meta()
    assert len(lst) > 0
    assert lst[0].startswith("X:")


def test_the_session_get_tune_collections():
    df = the_session.get_tune_collections(1)  # Cooley's
    assert not df.empty


def test_the_session_get_member_set():
    tunes = the_session.get_member_set(65013, 106212)
    assert len(tunes) == 3
    d = tunes[0]
    assert d["name"] == "Garech's Wedding"
    assert d["tune_id"] == 2620
    assert d["setting_id"] == 31341


def test_the_session_get_member_sets():
    sets = the_session.get_member_sets(65013)
    assert len(sets) >= 1
    d = sets[0][0]
    assert d["name"] == "Garech's Wedding"
    assert d["tune_id"] == 2620
    assert d["setting_id"] == 31341
