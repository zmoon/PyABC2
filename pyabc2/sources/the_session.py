"""
Load data from The Session (https://thesession.org)
"""
import logging
import sys
import warnings
from pathlib import Path
from typing import List, Optional, Union

from ..parse import Tune

logger = logging.getLogger(__name__)
sh = logging.StreamHandler(sys.stdout)
f = logging.Formatter(
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt=r"%d-%b-%Y %H:%M:%S",
)
sh.setFormatter(f)
logger.addHandler(sh)
del f, sh

HERE = Path(__file__).parent

SAVE_TO = HERE / "_the-session"

_TYPE_TO_METER = {
    "jig": "6/8",
    "reel": "4/4",
    "slip jig": "9/8",
    "hornpipe": "4/4",
    "polka": "2/4",
    "slide": "12/8",
    "waltz": "3/4",
    "barndance": "4/4",
    "strathspey": "4/4",
    "three-two": "3/2",
    "mazurka": "3/4",
    "march": "4/4",
}

_URL_NETLOCS = {"thesession.org"}


def _data_to_tune(data: dict) -> Tune:
    """Load one tune from a The Session JSON archive entry."""
    name = data["name"]
    type_ = data["type"]  # e.g. 'reel'
    melody_abc = data["abc"].replace("! ", "\n")
    key = data["mode"]
    meter = data["meter"]
    unit_length = "1/8"

    abc = f"""\
T:{name}
R:{type_}
M:{meter}
L:{unit_length}
K:{key}
{melody_abc}
"""

    return Tune(abc)


def load_url(url: str) -> Tune:
    """Load tune from a specified ``thesession.org`` URL.

    For example:
    - https://thesession.org/tunes/10000 (first setting assumed)
    - https://thesession.org/tunes/10000#setting31601 (specific setting)

    Using the API: https://thesession.org/api
    """
    from urllib.parse import urlsplit, urlunsplit

    import requests

    res = urlsplit(url)
    assert res.netloc in _URL_NETLOCS
    setting: Optional[int]
    if res.fragment:
        setting_str = res.fragment
        if setting_str.startswith("setting"):
            setting_str = setting_str[len("setting") :]
        setting = int(setting_str)
    else:
        setting = None
    to_query = urlunsplit(res._replace(scheme="https", fragment="", query="format=json"))

    r = requests.get(to_query)
    r.raise_for_status()
    data = r.json()

    if setting is None:
        # Use first
        d = data["settings"][0]
    else:
        for d in data["settings"]:
            if d["id"] == setting:
                break
        else:
            raise ValueError(f"detected setting {setting} not found in {to_query}")

    # Add non-setting-specific data
    assert "name" not in d
    assert "type" not in d
    assert "meter" not in d
    d.update(name=data["name"], type=data["type"], meter=_TYPE_TO_METER[data["type"]])

    # 'key' is 'mode' in the JSON data
    d["mode"] = d.pop("key")

    return _data_to_tune(d)


def download(which: Union[str, List[str]] = "tunes") -> None:
    import requests

    if isinstance(which, str):
        which = [which]

    SAVE_TO.mkdir(exist_ok=True)

    base_url = "https://github.com/adactio/TheSession-data/raw/main/json/"
    supported = ["tunes"]

    if not set(which) <= set(supported):
        raise ValueError(f"invalid `which`. Only these are supported: {supported}.")

    for fstem in which:  # TODO: threaded
        fn = f"{fstem}.json"
        url = base_url + fn
        r = requests.get(url)
        r.raise_for_status()
        with open(SAVE_TO / fn, "wb") as f:
            f.write(r.content)


def _maybe_load_one(d: dict) -> Tune:
    """Try to load tune from a The Session data entry, otherwise log debug messages
    and return None."""
    from textwrap import indent

    try:
        tune = _data_to_tune(d)
    except Exception as e:
        d_ = {k: v for k, v in d.items() if k in {"tune_id", "setting_id", "title"}}
        abc_ = indent(d["abc"], " ")
        logger.debug(f"Failed to load ({e}): {d_}\n{abc_}")
        tune = None

    return tune


def load(
    *, n: Optional[int] = None, redownload: bool = False, debug: bool = False, num_workers: int = 1
) -> List[Tune]:
    """Load tunes from https://github.com/adactio/TheSession-data

    Use ``redownload=True`` to force re-download. Otherwise the file will only
    be downloaded if it hasn't already been.

    @adactio (Jeremy) is the creator of The Session.
    """
    import json

    fp = SAVE_TO / "tunes.json"
    parallel = num_workers > 1

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.NOTSET)

    if not fp.is_file() or redownload:
        download("tunes")

    with open(fp, encoding="utf-8") as f:
        data = json.load(f)

    if n is not None:
        data = data[:n]

    if parallel:
        import multiprocessing

        if debug:
            warnings.warn("Multi-processing, detailed debug messages won't be shown.")

        with multiprocessing.Pool(num_workers) as pool:
            maybe_tunes = pool.map(_maybe_load_one, data)
    else:
        maybe_tunes = [_maybe_load_one(d) for d in data]

    tunes = []
    failed = 0
    for maybe_tune in maybe_tunes:
        if maybe_tune is None:
            failed += 1
        else:
            tunes.append(maybe_tune)

    if failed:
        msg = f"{failed} The Session tune(s) failed to load."
        if logger.level == logging.NOTSET or logger.level > logging.DEBUG:
            msg += " Enable logging debug messages to see more info."
        warnings.warn(msg)

    return tunes


def load_meta(which: str):
    """Load metadata file from The Session archive as dataframe (requires pandas).

    https://github.com/adactio/TheSession-data/tree/main/json
    """
    import pandas as pd

    allowed = ["aliases", "events", "recordings", "sessions", "sets", "tune_popularity", "tunes"]
    if which not in allowed:
        raise ValueError(f"invalid `which`. Valid choices: {allowed}.")

    base_url = "https://raw.githubusercontent.com/adactio/TheSession-data/main/json/"
    fn = f"{which}.json"
    url = base_url + fn

    df = pd.read_json(url)

    return df


if __name__ == "__main__":
    tune = load_url("https://thesession.org/tunes/10000")
    print(tune)
    tune.print_measures(4)

    tune = load_url("https://thesession.org/tunes/10000#31601")
    print(tune)
    tune.print_measures(5)

    tunes = load(n=200)
    for tune in tunes[:3]:
        print(tune)
        tune.print_measures(4)
