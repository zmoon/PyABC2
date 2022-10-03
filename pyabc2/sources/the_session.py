"""
Load data from The Session (https://thesession.org)
"""
from pathlib import Path

from ..parse import Tune

_TYPES = {
    "jig": (),
    "reel": (),
    "slip jig": (),
    "hornpipe": (),
    "polka": (),
    "slide": (),
    "waltz": (),
    "barndance": (),
    "strathspey": (),
    "three-two": (),
    "mazurka": (),
    "march": (),
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
    else:
        setting = Path(res.path).name
    setting = int(setting)
    to_query = urlunsplit(res._replace(scheme="https", fragment="", query="format=json"))

    r = requests.get(to_query)
    r.raise_for_status()
    data = r.json()

    for d in data["settings"]:
        if d["id"] == setting:
            break
    else:
        raise ValueError(f"detected setting {setting} not found in {to_query}")

    name = data["name"]
    type_ = data["type"]  # e.g. 'reel'
    melody_abc = d["abc"]
    key = d["key"]
    # TODO: provide guess for M? (based on type)

    abc = f"""\
T:{name}
R:{type_}
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
