"""
Henrik Norbeck's ABC Tunes

https://www.norbeck.nu/abc/
"""
from pathlib import Path
from typing import List, Union

from ..parse import Tune

HERE = Path(__file__).parent

SAVE_TO = HERE / "_norbeck"


def download() -> None:
    import io
    import zipfile

    import requests

    # All Norbeck, including non-Irish
    url = "https://www.norbeck.nu/abc/hn202110.zip"

    r = requests.get(url)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise Exception("Norbeck file unable to be downloaded (check URL).") from e

    SAVE_TO.mkdir(exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for info in z.infolist():
            fn0 = info.filename
            if fn0.startswith("i/") and not info.is_dir():
                fn = Path(info.filename).name
                with z.open(info) as zf, open(SAVE_TO / fn, "wb") as f:
                    f.write(zf.read())


_TYPE_PREFIX = {
    "reels": "hnr",
    "jigs": "hnj",
    "hornpipes": "hnhp",
    "polkas": "hnp",
    "slip jigs": "hnsj",
}


def _maybe_download() -> None:
    if not list(SAVE_TO.glob("*.abc")):
        print("downloading missing files...")
        download()


# https://en.wikibooks.org/wiki/LaTeX/Special_Characters#Escaped_codes
_COMBINING_ACCENT_FROM_ASCII_SYM = {
    "`": "\u0300",  # grave
    "'": "\u0301",  # acute
    "^": "\u0302",  # circumflex
    '"': "\u0308",  # umlaut
    "r": "\u030A",  # ring above
}


def _replace_escaped_diacritics(abc: str, *, ascii_only: bool = False) -> str:
    """Load a Norbeck ABC, dealing with LaTeX-style diacritic escape codes."""
    import re

    # Special case: `\aa` command for ring over a
    abc1 = abc
    abc1 = re.sub(r"\{?\\aa\}?", "å", abc1)

    # Special case: `\o` command for slashed o
    abc1 = re.sub(r"\{?\\o\}?", "ø", abc1)

    # Accents added to letters
    abc2 = abc1
    for m in re.finditer(r"\\(?P<dcsym>.)\{?(?P<letter>[a-zA-Z])\}?", abc1):
        s = m.group(0)

        gd = m.groupdict()
        dcsym = gd["dcsym"]
        letter = gd["letter"]

        ca = _COMBINING_ACCENT_FROM_ASCII_SYM.get(dcsym)
        if ca is None:
            raise ValueError(
                f"diacritic escape code `\\{dcsym}` not recognized "
                f"in this ABC:\n---\n{abc}\n---"
            )

        if ascii_only:
            snew = letter
        else:
            snew = letter + ca
            # Note: could use unicodedata to apply a normalization
            # to give single accented characters instead of two code points

        abc2 = abc2.replace(s, snew)

    return abc2


def _load_one_file(fp: Path, *, ascii_only: bool = False) -> List[Tune]:
    """Load one of the Norbeck archive files, which contain multiple tunes."""

    blocks = []
    with open(fp, "r") as f:

        block = ""
        iblock = -1
        add = False
        in_header = True

        for line in f:
            if line.startswith("X:"):
                # New tune, reset
                block = line
                iblock += 1
                add = True
                in_header = False
                continue

            if line.startswith("P:"):
                # Variations, skip and wait until next block
                add = False

            if add:
                block += line

            if line.strip() == "" and not in_header:
                # Between tune blocks, save
                blocks.append(block.strip())

    tunes: List[Tune] = []
    for abc0 in blocks:
        try:
            tunes.append(Tune(_replace_escaped_diacritics(abc0, ascii_only=ascii_only)))
        except Exception as e:
            raise Exception(f"loading this ABC:\n---\n{abc0}\n---\nfailed") from e

    # Add norbeck.nu/abc/ URLs
    for tune in tunes:
        # Example: https://www.norbeck.nu/abc/display.asp?rhythm=reel&ref=10
        ref = tune.header["reference number"]
        rhy = tune.type
        tune.url = f"https://www.norbeck.nu/abc/display.asp?rhythm={rhy}&ref={ref}"

    return tunes


def load(which: Union[str, List[str]] = "all", *, ascii_only: bool = False) -> List[Tune]:
    """
    Load a list of tunes, by type(s) or all of them.

    Parameters
    ----------
    which
        reels, jigs, hornpipes,
    ascii_only
        Whether to drop the implied diacritic symbols, e.g., `\'o` (`True`)
        or add the corresponding unicode characters (`False`).
    """
    # TODO: allow Norbeck ID as arg as well to load an individual tune? or URL?
    if isinstance(which, str):
        which = [which]

    _maybe_download()

    fps: List[Path]
    if which == ["all"]:
        fps = list(SAVE_TO.glob("*.abc"))

    else:
        fps = []
        for tune_type in which:

            if tune_type not in _TYPE_PREFIX:
                raise ValueError(
                    f"tune type {tune_type!r} invalid or not supported. "
                    f"Try one of: {', '.join(repr(s) for s in _TYPE_PREFIX)}."
                )

            fps.extend(SAVE_TO.glob(f"{_TYPE_PREFIX[tune_type]}*.abc"))

    tunes = []
    for fp in sorted(fps):
        tunes.extend(_load_one_file(fp, ascii_only=ascii_only))

    return tunes


def load_url(url: str) -> Tune:
    """Load tune from a specified ``norbeck.nu/abc/`` URL.

    For example:
    - https://norbeck.nu/abc/display.asp?rhythm=slip+jig&ref=106
    - https://www.norbeck.nu/abc/display.asp?rhythm=reel&ref=693

    Grabs the ABC from the HTML source.
    """
    import re
    from html import unescape
    from urllib.parse import urlsplit, urlunsplit

    import requests

    res = urlsplit(url)
    assert res.netloc in {"norbeck.nu", "www.norbeck.nu"}
    assert res.path.startswith("/abc")

    r = requests.get(urlunsplit(res._replace(scheme="https")))
    r.raise_for_status()

    m = re.search(
        r'<div id="abc" class="monospace">X:[0-9]+<br/>\s*(.*?)\s*</div>', r.text, flags=re.DOTALL
    )
    assert m is not None
    abc = unescape(m.group(1)).replace("<br/>", "")

    return Tune(abc)


if __name__ == "__main__":
    tune = load_url("https://norbeck.nu/abc/display.asp?rhythm=slip+jig&ref=106")
    print(tune.title)
    tune.print_measures(5)

    tune = load_url("https://www.norbeck.nu/abc/display.asp?rhythm=sl%C3%A4ngpolska&ref=8")
    print()
    print(tune.title)
    tune.print_measures(5)
    print(tune.abc)
