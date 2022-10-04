"""
Load data from The Session (https://thesession.org)
"""
from ..parse import Tune

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

    name = data["name"]
    type_ = data["type"]  # e.g. 'reel'
    melody_abc = d["abc"].replace("! ", "\n")
    assert "!" not in melody_abc
    key = d["key"]
    meter = _TYPE_TO_METER[type_]
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


if __name__ == "__main__":
    tune = load_url("https://thesession.org/tunes/10000")
    print(tune)
    tune.print_measures()

    tune = load_url("https://thesession.org/tunes/10000#31601")
    print(tune)
    tune.print_measures()
