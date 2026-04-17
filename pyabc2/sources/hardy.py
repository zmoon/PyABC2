"""
Load data from Paul Hardy's tunebooks (https://pghardy.net/tunebooks/).

Requires:

* `requests <https://requests.readthedocs.io/>`__
"""

import re
from pathlib import Path
from typing import Literal

HERE = Path(__file__).parent

SAVE_TO = HERE / "_hardy"

_BASE_URL = "https://pghardy.net/tunebooks/"

_TUNEBOOK_KEY_TO_URL = {
    "session": _BASE_URL + "pgh_session_tunebook.abc",
    "annex": _BASE_URL + "pgh_annex_tunebook.abc",
    "basic": _BASE_URL + "pgh_basic_tunebook.abc",
    "xmas": _BASE_URL + "pgh_xmas_tunebook.abc",
    "possible": _BASE_URL + "pgh_possible_tunebook.abc",
    "pete_mac": _BASE_URL + "pgh_pete_mac_tunebook.abc",
    "clarke": _BASE_URL + "williamclarke_tunes.abc",
}


def download(key: str) -> None:
    """Download the ABC file for the given tunebook key and cache it."""
    import requests

    key = key.lower()
    try:
        url = _TUNEBOOK_KEY_TO_URL[key]
    except KeyError:
        raise ValueError(
            f"Unknown Hardy tunebook key: {key!r}. Valid options: {sorted(_TUNEBOOK_KEY_TO_URL)}."
        ) from None

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    SAVE_TO.mkdir(exist_ok=True)
    (SAVE_TO / f"{key}.abc").write_text(r.text, encoding="utf-8")


def load_meta(
    key: str,
    *,
    redownload: bool = False,
    remove_prefs: str | tuple[str, ...] | Literal[False] = ("%",),
) -> list[str]:
    """Load ABC tune blocks from a Paul Hardy tunebook, no parsing.

    Parameters
    ----------
    key
        Tunebook key.

        .. list-table::
           :header-rows: 1
           :widths: 15 85

           * - Key
             - Description
           * - ``session``
             - Paul Hardy's Session Tunebook (the main tunebook)
           * - ``annex``
             - Paul Hardy's Annex Tunebook (current edition; tunes awaiting next session edition)
           * - ``basic``
             - Paul Hardy's Basic Tunebook (subset of simpler/common session tunes)
           * - ``xmas``
             - Paul Hardy's Xmas Tunebook (Christmas tunes and carols)
           * - ``possible``
             - Paul Hardy's Possible Tunebook (tunes not yet fully learned)
           * - ``pete_mac``
             - Paul Hardy's Pete Mac Tunebook (CC0 tunes by Pete Mac)
           * - ``clarke``
             - William Clarke of Feltwell Tunebook (19th century East Anglian manuscript)

        See https://pghardy.net/tunebooks/ for more information.
    redownload
        Re-download the data file.
    remove_prefs
        Remove lines starting with these prefixes (applied at load time; cached file is unmodified).
        Defaults to ``("%",)``, which strips all ``%`` comment and ``%%`` directive lines.
        Pass ``False`` or ``()`` to keep all lines.

    See Also
    --------
    :doc:`/examples/sources`
    """
    key = key.lower()
    if key not in _TUNEBOOK_KEY_TO_URL:
        raise ValueError(
            f"Unknown Hardy tunebook key: {key!r}. Valid options: {sorted(_TUNEBOOK_KEY_TO_URL)}."
        )

    if redownload or not (SAVE_TO / f"{key}.abc").is_file():
        print("downloading...", end=" ", flush=True)
        download(key)
        print("done")

    # Read as binary to avoid universal-newlines mangling of \r\r\n (Hardy's line ending)
    # and then convert to \n.
    text = (SAVE_TO / f"{key}.abc").read_bytes().decode("utf-8").replace("\r", "")

    if not remove_prefs:
        remove_prefs = ()
    elif isinstance(remove_prefs, str):
        remove_prefs = (remove_prefs,)

    # Split into tune blocks by finding X: at start of line
    # (Each tune block begins with X:)
    parts = re.split(r"(?m)^(?=X:)", text)
    abcs = []
    for part in parts:
        part = part.strip()
        if not part.startswith("X:"):
            continue

        # Strip trailing % directives unconditionally
        lines = part.splitlines()
        while lines and lines[-1].lstrip().startswith("%"):
            lines.pop()
        part = "\n".join(lines).strip()

        if not part:
            continue

        if remove_prefs:
            lines = [
                line for line in part.splitlines() if not line.lstrip().startswith(remove_prefs)
            ]
            part = "\n".join(lines).strip()

        if part:
            abcs.append(part)

    return abcs
