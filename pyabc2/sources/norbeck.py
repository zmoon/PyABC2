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
    url = "https://www.norbeck.nu/abc/hn201912.zip"

    r = requests.get(url)

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


def _load_one_file(fp: Path) -> List[Tune]:

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

    tunes = []
    for abc in blocks:

        try:
            tunes.append(Tune(abc))

        except Exception as e:
            raise Exception(f"loading this ABC:\n---\n{abc}\n---\nfailed") from e

    return tunes


# TODO: ASCII accent mark notation to unicode (+ stripped version)?


def load(which: Union[str, List[str]] = "all") -> List[Tune]:
    """
    Load a list of tunes, by type(s) or all of them.

    Parameters
    ----------
    which
        reels, jigs, hornpipes,
    """
    if isinstance(which, str):
        which = [which]

    _maybe_download()

    if which == ["all"]:
        fps = SAVE_TO.glob("*.abc")

    else:
        for tune_type in which:

            if tune_type not in _TYPE_PREFIX:
                raise ValueError(
                    f"tune type {tune_type!r} invalid or not supported. "
                    f"Try one of: {', '.join(repr(s) for s in _TYPE_PREFIX)}."
                )

            fps = SAVE_TO.glob(f"{_TYPE_PREFIX[tune_type]}*.abc")

    tunes = []
    for fp in fps:
        tunes.extend(_load_one_file(fp))

    return tunes
