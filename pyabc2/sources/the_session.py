"""
Load data from The Session (https://thesession.org)
"""
import logging
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, List, Literal, Optional, Union

from .._util import get_logger as _get_logger
from ..parse import Tune

if TYPE_CHECKING:  # pragma: no cover
    import pandas

_DEBUG_SHOW_FULL_ABC = os.getenv("PYABC_DEBUG_SHOW_FULL_ABC", False)

logger = _get_logger(__name__)

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


def _api_data_to_tune(data: dict) -> Tune:
    """The Session Web API tune/setting data -> Tune"""
    melody_abc = data["abc"].replace("! ", "\n")

    # 'x' - setting number (for a specific tune; not same as setting ID)
    # note: tune data has 'aliases', could use to provide additional T's (or set `titles` after init)
    abc = f"""\
X:{data['x']}
T:{data['name']}
R:{data['type']}
M:{data['meter']}
L:1/8
K:{data['key']}
{melody_abc}
"""

    tune = Tune(abc)
    tune.url = f"https://thesession.org/tunes/{data['tune_id']}#setting{data['setting_id']}"

    return tune


def _archive_data_to_tune(data: dict) -> Tune:
    """The Session JSON archive entry -> Tune"""
    # Differences cf. to the web API data:
    # - don't know X
    # - don't need to convert `! ` to newline
    # - 'key' is 'mode'
    # - the archive data entries have 'tune_id' and 'setting_id' already

    melody_abc = data["abc"]

    abc = f"""\
T:{data['name']}
R:{data['type']}
M:{data['meter']}
L:1/8
K:{data['mode']}
{melody_abc}
"""

    tune = Tune(abc)
    tune.url = f"https://thesession.org/tunes/{data['tune_id']}#setting{data['setting_id']}"

    return tune


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
    tune_data = r.json()

    if setting is None:
        # Use first
        i = 0
        setting_data = tune_data["settings"][i]
    else:
        for i, setting_data in enumerate(tune_data["settings"]):
            if setting_data["id"] == setting:
                break
        else:  # pragma: no cover
            raise ValueError(f"detected setting {setting} not found in {to_query}")

    # Add non-setting-specific data
    assert "name" not in setting_data
    assert "type" not in setting_data
    assert "meter" not in setting_data
    setting_data.update(
        name=tune_data["name"],
        type=tune_data["type"],
        meter=_TYPE_TO_METER[tune_data["type"]],
        x=i + 1,
    )

    # Add IDs
    setting_data["setting_id"] = setting_data.pop("id")
    setting_data["tune_id"] = tune_data["id"]

    return _api_data_to_tune(setting_data)


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


def _maybe_load_one(d: dict) -> Optional[Tune]:
    """Try to load tune from a The Session data entry, otherwise log debug messages
    and return None."""
    from textwrap import indent

    d["abc"] = d["abc"].replace("\r\n", "\n")
    try:
        tune = _archive_data_to_tune(d)
    except Exception as e:  # pragma: no cover
        d_ = {k: v for k, v in d.items() if k in {"tune_id", "setting_id", "title"}}
        msg = f"Failed to load ABC ({e}): {d_}"
        if _DEBUG_SHOW_FULL_ABC:
            abc_ = indent(d["abc"], "  ")
            msg += f"\n{abc_}"
        logger.debug(msg)
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

    if debug:  # pragma: no cover
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

        if debug:  # pragma: no cover
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
        msg = f"{failed} out of {len(data)} The Session tune(s) failed to load."
        if logger.level == logging.NOTSET or logger.level > logging.DEBUG:
            msg += " Enable logging debug messages to see more info."
        warnings.warn(msg)

    return tunes


def _choose_int_type(s, *, ext: bool = False):
    import numpy as np

    s_max = s.max()
    s_hasneg = (s < 0).any()

    # TODO: DRY (generate `to_try` list?)
    i8_max = np.iinfo(np.int8).max
    i16_max = np.iinfo(np.int16).max
    i32_max = np.iinfo(np.int32).max
    i64_max = np.iinfo(np.int64).max

    ui8_max = np.iinfo(np.uint8).max
    ui16_max = np.iinfo(np.uint16).max
    ui32_max = np.iinfo(np.uint32).max
    ui64_max = np.iinfo(np.uint64).max

    if s_hasneg:
        to_try = [
            (i8_max, np.int8, "Int8"),
            (i16_max, np.int16, "Int16"),
            (i32_max, np.int32, "Int32"),
            (i64_max, np.int64, "Int64"),
        ]
    else:
        to_try = [
            (ui8_max, np.uint8, "UInt8"),
            (ui16_max, np.uint16, "UInt16"),
            (ui32_max, np.uint32, "UInt32"),
            (ui64_max, np.uint64, "UInt64"),
        ]

    for max_, typ, ext_typ_str in to_try:
        if s_max <= max_:
            break
    else:  # pragma: no cover
        raise AssertionError("shouldn't reach here")

    return ext_typ_str if ext else typ


def load_meta(
    which: str,
    *,
    convert_dtypes: bool = False,
    downcast_ints: bool = False,
    format: Literal["json", "csv"] = "json",
) -> "pandas.DataFrame":
    """Load metadata file from The Session archive as dataframe (requires pandas).

    In string columns (dtype ``object``), missing value is ``''`` (empty string)
    and is currently left that way by default.
    However, if ``convert_dtypes=True`` is used, this will be set to null,
    and dtypes converted to nullable pandas extension types
    (:meth:`pandas.DataFrame.convert_dtypes` applied).

    https://github.com/adactio/TheSession-data/tree/main/json
    https://github.com/adactio/TheSession-data/tree/main/csv

    @adactio (Jeremy) is the creator of The Session.
    """
    import numpy as np
    import pandas as pd

    allowed = ["aliases", "events", "recordings", "sessions", "sets", "tune_popularity", "tunes"]
    if which not in allowed:
        raise ValueError(f"invalid `which`. Valid choices: {allowed}.")

    if format not in {"csv", "json"}:
        raise ValueError("`format` must be 'csv' or 'json'.")

    base_url = f"https://raw.githubusercontent.com/adactio/TheSession-data/main/{format}/"
    fn = f"{which}.{format}"
    url = base_url + fn

    if format == "json":
        df = pd.read_json(url)
    else:
        parse_dates: Union[bool, List[str]]
        if which in {"sets", "sessions", "tunes"}:
            parse_dates = ["date"]
        elif which in {"events"}:
            parse_dates = ["dtstart", "dtend"]
        else:
            parse_dates = False
        df = pd.read_csv(url, parse_dates=parse_dates, keep_default_na=False)

    cat_cols = []
    if which == "aliases":
        pass

    elif which == "events":
        df["dtstart"] = pd.to_datetime(df.dtstart)
        df["dtend"] = pd.to_datetime(df.dtend)
        df["latitude"] = df.latitude.replace("", np.nan).astype(float)
        df["longitude"] = df.longitude.replace("", np.nan).astype(float)

    elif which == "recordings":
        # Note 'tune_id' can be missing, so is left as str
        # To get int with missing val support: `.tune_id.replace("", np.nan).astype("UInt16")`
        pass

    elif which == "sessions":
        pass

    elif which == "sets":
        # int cols: 'tuneset', 'member_id', 'settingorder', 'tune_id', 'setting_id'
        cat_cols = ["type", "meter", "mode"]

    elif which == "tune_popularity":
        # str cols: 'name', 'tunebooks'
        # int cols: 'tune_id'
        # Currently min tunebook count ('tunebooks') is 10
        # (https://github.com/adactio/TheSession-data/issues/14)
        pass

    elif which == "tunes":
        # int cols: 'tune_id', 'setting_id'
        cat_cols = ["type", "meter", "mode"]

    else:  # pragma: no cover
        raise AssertionError("shouldn't reach here")

    if downcast_ints:
        int_cols = df.dtypes[df.dtypes == np.int64].index.tolist()
        for col in int_cols:
            df[col] = df[col].astype(_choose_int_type(df[col], ext=False))

    if convert_dtypes:
        df = df.replace("", np.nan)

        # Special case for recordings 'tune_id'
        if which == "recordings":
            df["tune_id"] = df["tune_id"].astype(
                "Int64"
                if not downcast_ints
                else _choose_int_type(df.tune_id.dropna().astype(np.int64), ext=True)
            )

        df = df.convert_dtypes()
        df[cat_cols] = df[cat_cols].astype("category")

    return df


if __name__ == "__main__":  # pragma: no cover
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
