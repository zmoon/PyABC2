"""
Load data from the Eskin ABC Transcription Tools tunebook websites
(https://michaeleskin.com/tunebooks.html).

Requires:

* `requests <https://requests.readthedocs.io/>`__
"""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, Tuple, Union
from urllib.parse import parse_qs, urlsplit

from pyabc2 import Tune
from pyabc2.sources._lzstring import LZString

if TYPE_CHECKING:  # pragma: no cover
    import pandas

HERE = Path(__file__).parent

SAVE_TO = HERE / "_eskin"

_TBWS = "https://michaeleskin.com/tunebook_websites"
_CCE_SD = "https://michaeleskin.com/cce_sd"
_TUNEBOOK_KEY_TO_URL = {
    # https://michaeleskin.com/tunebooks.html#websites_irish
    "kss": f"{_TBWS}/king_street_sessions_tunebook_17Jan2025.html",
    "oflaherty_2025": f"{_TBWS}/oflahertys_2025_retreat_tunes_final.html",
    "carp": f"{_TBWS}/carp_celtic_jam_tunebook_17Jan2025.html",
    "hardy_2024": f"{_TBWS}/paul_hardy_2024_8feb2025.html",
    "hardy_2025": f"{_TBWS}/paul_hardy_2025_12aug2025.html",
    "cce_dublin_2001": f"{_CCE_SD}/cce_dublin_2001_tunebook_17Jan2025.html",
    "cce_san_diego_jan2025": f"{_CCE_SD}/cce_san_diego_tunes_31jan2025.html",
    "cce_san_diego_nov2025": f"{_CCE_SD}/cce_san_diego_tunes_10nov2025.html",
    # https://michaeleskin.com/tunebooks.html#websites_18th_century_collections
    "aird": f"{_TBWS}/james_aird_campin_18jan2025.html",
    "playford1": f"{_TBWS}/playford_1_partington_17jan2025.html",
    "playford2": f"{_TBWS}/playford_2_partington_17jan2025.html",
    "playford3": f"{_TBWS}/playford_3_partington_20jan2025.html",
}
"""Mapping of tunebook keys (defined here, not by Eskin; e.g. 'kss' for King Street Sessions)
to tunebook website URLs, which come from this page:
https://michaeleskin.com/tunebooks.html
"""

# Definitive versions
_TUNEBOOK_ALIAS = {
    "cce_san_diego": "cce_san_diego_nov2025",
}
for _alias, _target in _TUNEBOOK_ALIAS.items():
    _TUNEBOOK_KEY_TO_URL[_alias] = _TUNEBOOK_KEY_TO_URL[_target]

_URL_NETLOCS = {"michaeleskin.com", "www.michaeleskin.com"}


def abctools_url_to_abc(
    url: str,
    *,
    remove_prefs: Union[str, Tuple[str, ...], Literal[False]] = (
        r"%%titlefont ",
        r"%%subtitlefont ",
        r"%%infofont ",
        r"%%partsfont ",
        r"%%textfont ",
        r"%%tempofont ",
        r"%irish_rolls_on",
        r"%swing",
        r"%abcjs_",
        r"%%MIDI ",
        r"%add_all_playback_links",
    ),
) -> str:
    """Extract the ABC from an Eskin abctools (``michaeleskin.com/abctools/``) share URL.

    More info: https://michaeleskin.com/tools/generate_share_link.html

    Parameters
    ----------
    remove_prefs
        Remove lines starting with these prefixes.
        Use ``False`` or an empty iterable to keep all lines instead.
    """

    if not remove_prefs:
        remove_prefs = ()
    elif isinstance(remove_prefs, str):
        remove_prefs = (remove_prefs,)

    res = urlsplit(url)
    assert res.netloc in _URL_NETLOCS
    assert res.path.startswith("/abctools/")

    query_params = parse_qs(res.query)
    try:
        (lzw,) = query_params["lzw"]
    except Exception as e:
        raise ValueError("URL does not contain required 'lzw' parameter") from e
    # Note `+` has been replaced with space by parse_qs
    # Note js LZString.compressToEncodedURIComponent() is used to compress/encode the ABC

    abc = LZString.decompressFromEncodedURIComponent(lzw)
    if abc is None:
        raise RuntimeError("Failed to decompress LZString data")

    wanted_lines = [
        line.strip() for line in abc.splitlines() if not line.lstrip().startswith(remove_prefs)
    ]

    return "\n".join(wanted_lines)


def abc_to_abctools_url(abc: str) -> str:
    """Create an Eskin abctools (``michaeleskin.com/abctools/``) share URL for `abc`.

    More info: https://michaeleskin.com/tools/generate_share_link.html
    """

    # Must start with 'X:' (seems value is not required)
    if not abc.lstrip().startswith("X"):
        abc = "X:\n" + abc

    lzw = LZString.compressToEncodedURIComponent(abc)

    return f"https://michaeleskin.com/abctools/abctools.html?lzw={lzw}"


class EskinTunebookInfo(NamedTuple):
    key: str
    url: str
    stem: str
    path: Path


def get_tunebook_info(key: str) -> EskinTunebookInfo:
    try:
        url = _TUNEBOOK_KEY_TO_URL[key.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown Eskin tunebook key: {key!r}. Valid options: {sorted(_TUNEBOOK_KEY_TO_URL)}."
        ) from None
    stem = Path(urlsplit(url).path).stem

    return EskinTunebookInfo(
        key=key,
        url=url,
        stem=stem,
        path=SAVE_TO / f"{stem}.json.gz",
    )


def _download_data(key: str):
    """Extract and save the tune data from the tunebook webpage as JSON."""
    import gzip

    import requests

    tb_info = get_tunebook_info(key)

    r = requests.get(tb_info.url, timeout=5)
    r.raise_for_status()
    html = r.text

    # First find the tune type options by searching for 'tunes = type;'
    types = sorted(set(re.findall(r"tunes = (.*?);", html)))
    if types:
        pass
    elif "const tunes=[" in html:  # no types, just one list of tunes
        types = ["tunes"]
    else:
        raise RuntimeError("Unable to detect tune types")

    # Then the data are in like `const reels=[{...}, ...];`
    all_data = {}
    for type_ in types:
        m = re.search(rf"const {type_}=\[(.*?)\];", html, flags=re.DOTALL)
        if m is None:
            raise RuntimeError(f"Unable to find data for type {type_!r}")
        s_data = "[" + m.group(1) + "]"

        try:
            data = json.loads(s_data)
        except json.JSONDecodeError as e:
            print(s_data[e.pos], "context:", s_data[e.pos - 10 : e.pos + 10])
            raise

        for d in data:
            assert d.keys() == {"Name", "URL"}
            d["name"] = d.pop("Name")
            d["abc"] = abctools_url_to_abc(d.pop("URL"))

        all_data[type_] = data

    SAVE_TO.mkdir(exist_ok=True)
    with gzip.open(tb_info.path, "wt") as f:
        json.dump(all_data, f, indent=2)


def _load_data(key: str):
    """Load the data from the saved JSON."""
    import gzip

    with gzip.open(get_tunebook_info(key).path, "rt") as f:
        return json.load(f)


def load_meta(key: str, *, redownload: bool = False) -> "pandas.DataFrame":
    """Load the tunebook data, no parsing.

    Parameters
    ----------
    key
        Tunebook key (ID), e.g. ``'kss'`` for King Street Sessions.

        .. list-table::
           :header-rows: 1
           :widths: 15 85

           * - Key
             - Description
           * - ``aird``
             - James Aird's Airs by Jack Campin
           * - ``carp``
             - CARP Celtic Jam Tunebook
           * - ``cce_dublin_2001``
             - CCE Dublin 2001
           * - ``cce_san_diego``
             - CCE San Diego
           * - ``hardy_{2024,2025}``
             - Paul Hardy's Session Tunebook
           * - ``kss``
             - King Street Sessions Tunebook
           * - ``oflaherty_2025``
             - O'Flaherty's Retreat Tunes
           * - ``playford{1,2,3}``
             - Playford vols. 1--3

        See https://michaeleskin.com/tunebooks.html
        for more information.

    See Also
    --------
    :doc:`/examples/sources`
    """
    import pandas as pd

    tb_info = get_tunebook_info(key)

    fp = tb_info.path
    if not fp.is_file() or redownload:
        print("downloading...", end=" ", flush=True)
        _download_data(key)
        print("done")

    data = _load_data(key)

    dfs = []
    for group, tunes in data.items():
        df_ = pd.DataFrame(tunes)
        df_["group"] = group
        dfs.append(df_)
    df = pd.concat(dfs, ignore_index=True)

    return df


def load_url(url: str) -> Tune:
    """Load tune from an Eskin abctools (``michaeleskin.com/abctools/``) share URL.

    Notes
    -----
    The ABC is encoded in the URL, so we don't need to load the page.
    """
    abc = abctools_url_to_abc(url)
    return Tune(abc)


if __name__ == "__main__":  # pragma: no cover
    from . import load_example_abc

    abc = load_example_abc("For the Love of Music")
    url = abc_to_abctools_url(abc)
    print(url)

    kss = load_meta("kss")
    print(kss.keys())
