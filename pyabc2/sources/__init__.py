"""
Sources of ABC
"""
from typing import Optional

from ..parse import Tune

examples = {
    # https://www.norbeck.nu/abc/display.asp?rhythm=slip%20jig&ref=106
    # some header lines and variations removed
    "for the love of music": """\
T:For The Love Of Music
R:slip jig
C:Liz Carroll
M:9/8
L:1/8
K:G
GED DEG AGB | AGG GBd edd | GED DEG AGc | Bee BAB GEE :|
ged e/f/gB GB/c/d | ged egb a2f | ged e/f/gB AB/c/d | edB dBG ABd |
ged e/f/gB GB/c/d | ged egb a2a | bee e/f/ge a2g | edB dBG ABA ||
""",
    # http://www.norbeck.nu/abc/display.asp?rhythm=jig&ref=156
    # some header lines removed
    "tell her i am": """\
T:Tell Her I Am
R:jig
M:6/8
K:G
d|edB GAB|~D3 GAB|~D3 cBA|AGE GBd|edB GAB|~D3 GAB|~D3 cBA|AGF G2:|
|:c|~B3 def|gfe dBG|~A3 AGA|BAG ~E3|1 ~B3 def|gfe dBG|
~A3 cBA|AGF G2:|2 ~g3 aga|bge dBG|~A3 cBA|AGF G2||
""",
}


def load_example_abc(title: Optional[str] = None) -> str:
    """Load a random example ABC if `title` not provided.
    Case ignored in the title.
    """
    if title is None:
        import random

        k = random.choice(list(examples))
    else:
        k = title.lower()

    abc = examples.get(k)

    if abc is None:
        example_list = "\n".join(f"  - {t!r}" for t in examples)
        raise ValueError(
            f"invalid tune title {title!r}. "
            f"Valid options are (case-insensitive):\n{example_list}"
        )

    return abc


def load_example(title: Optional[str] = None) -> Tune:
    """Load an example tune,
    random if `title` not provided.
    Case ignored in the title.
    """
    return Tune(load_example_abc(title))


def load_url(url: str) -> Tune:
    """Load tune from ABC corresponding to `url`.

    Currently these URL types are supported:
    - Norbeck (``norbeck.nu/abc/``)
    - The Session (``thesession.org``)
    """
    from urllib.parse import urlsplit

    from . import norbeck, the_session

    res = urlsplit(url)
    if res.netloc in norbeck._URL_NETLOCS:
        return norbeck.load_url(url)
    elif res.netloc in the_session._URL_NETLOCS:
        return the_session.load_url(url)
    else:
        raise NotImplementedError("loading URL from {res.netloc} not implemented.")
