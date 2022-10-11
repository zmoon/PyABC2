"""
Load data from The Session (https://thesession.org)
"""
from pathlib import Path
from typing import List, Union

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


def _data_to_tune(data):
    name = data["name"]
    type_ = data["type"]  # e.g. 'reel'
    melody_abc = data["abc"].replace("! ", "\n")
    assert "!" not in melody_abc
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
    if res.fragment:
        setting = res.fragment
        if setting.startswith("setting"):
            setting = setting[len("setting") :]
        setting = int(setting)
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


def load() -> List[Tune]:
    """Load tunes from https://github.com/adactio/TheSession-data

    @adactio (Jeremy) is the creator of The Session.
    """
    import json

    fp = SAVE_TO / "tunes.json"
    if not fp.is_file():
        download("tunes")

    with open(fp, encoding="utf-8") as f:
        data = json.load(f)

    print(len(data), "tune dicts in this data dump")
    data = data[:5]
    for d in data:
        print(d)

    # TODO: multi-proc
    tunes = [_data_to_tune(d) for d in data]

    return tunes


if __name__ == "__main__":
    tune = load_url("https://thesession.org/tunes/10000")
    print(tune)
    tune.print_measures(4)

    tune = load_url("https://thesession.org/tunes/10000#31601")
    print(tune)
    tune.print_measures(5)

    tunes = load()
    for tune in tunes[:2]:
        print(tune)
        tune.print_measures(4)
