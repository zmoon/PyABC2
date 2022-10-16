"""
Load data from The Session (https://thesession.org)
"""
from pathlib import Path
from typing import List, Optional, Union

from ..parse import Tune

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

_URL_NETLOCS = {
    "thesession.org",
}


def _data_to_tune(data):
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
        raise ValueError(f"invalid `which`. Only these are supported: {supported}")

    for fstem in which:  # TODO: threaded
        fn = f"{fstem}.json"
        url = base_url + fn
        r = requests.get(url)
        r.raise_for_status()
        with open(SAVE_TO / fn, "wb") as f:
            f.write(r.content)


def load(*, n: Optional[int] = None, redownload: bool = False) -> List[Tune]:
    """Load tunes from https://github.com/adactio/TheSession-data

    Use ``redownload=True`` to force re-download. Otherwise the file will only
    be downloaded if it hasn't already been.

    @adactio (Jeremy) is the creator of The Session.
    """
    import json

    fp = SAVE_TO / "tunes.json"

    if not fp.is_file() or redownload:
        download("tunes")

    with open(fp, encoding="utf-8") as f:
        data = json.load(f)

    data = data[:n]

    # TODO: multi-proc
    # tunes = [_data_to_tune(d) for d in data]
    tunes = []
    failed = 0
    for d in data:
        try:
            tune = _data_to_tune(d)
        except Exception:
            failed += 1
        else:
            tunes.append(tune)

    print(failed, "failed")

    return tunes


if __name__ == "__main__":
    tune = load_url("https://thesession.org/tunes/10000")
    print(tune)
    tune.print_measures(4)

    tune = load_url("https://thesession.org/tunes/10000#31601")
    print(tune)
    tune.print_measures(5)

    tunes = load(n=3)
    for tune in tunes:
        print(tune)
        tune.print_measures(4)
