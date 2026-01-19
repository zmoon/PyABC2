"""
Bill Black's Irish Traditional Tune Library

http://www.capeirish.com/ittl/

As of the 2025-06-14 update, the "tunefolders" method is deprecated.
Bill Black is now using the Eskin ABC Tools (http://www.capeirish.com/ittl/alltunes/html/),
while also posting ABC text files (http://www.capeirish.com/ittl/alltunes/text/),
both split up alphabetically by tune name.
"""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from pyabc2._util import get_logger as _get_logger

logger = _get_logger(__name__)

HERE = Path(__file__).parent

ITTL = "http://www.capeirish.com/ittl/"
SAVE_TO = HERE / "_bill-black_tunefolders"


@dataclass
class Collection:
    key: str
    title: str
    folder: str
    subfolders: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)

    @property
    def abc_urls(self) -> list[str]:
        if self.urls:
            return self.urls
        else:
            num = self.folder
            if self.subfolders:
                return [
                    f"{ITTL}tunefolders/{num}/{subfolder}/{subfolder}-ABC.rtf"
                    for subfolder in self.subfolders
                ]
            else:
                return [f"{ITTL}tunefolders/{num}/{num}-ABC.rtf"]

    @property
    def files(self) -> list[Path]:
        return [self.url_to_file(url) for url in self.abc_urls]

    def url_to_file(self, url: str) -> Path:
        """Convert a URL to a file path."""
        return SAVE_TO / f"{url.split('/')[-1]}.gz"


COLLECTIONS: list[Collection] = [
    Collection(
        key="aif",
        title="Allan's Irish Fiddler",
        folder="11",
    ),
    Collection(
        key="bbmg",
        title="BB's Mostly Gems",
        folder="12",
        subfolders=["12-AE", "12-FJ", "12-KQ", "12-RST", "12-UY"],
    ),
    Collection(
        key="bs",
        title="Bulmer & Sharpley",
        folder="13",
        subfolders=["13-hps", "13-jigs", "13-misc", "13-p&s", "13-reels", "13-sjigs"],
    ),
    Collection(
        key="car",
        title="Carolan Tunes",
        folder="14",
    ),
    Collection(
        key="cre",
        title="Ceol Rince na hÉireann",
        folder="18",
        subfolders=["18-hornpipes", "18-jigs", "18-polkas_slides", "18-reels", "18-slipjigs"],
    ),
    Collection(
        key="dmi",
        title="Dance Music of Ireland",
        folder="21",
        subfolders=["hps", "jigs", "reels", "slipjigs"],
    ),
    Collection(
        key="dmwc",
        title="Dance Music of Willie Clancy",
        folder="22",
        subfolders=["22-hps", "22-jigs", "22-misc", "22-reels", "22-sjigs"],
    ),
    Collection(
        key="foinn",
        title="Foinn Seisiún",
        folder="25",
        subfolders=["hps", "jigs", "misc", "p&s", "reels"],
    ),
    Collection(
        key="jol",
        title="Johnny O'Leary of Sliabh Luachra",
        folder="31",
        subfolders=["31-hps", "31-jigs", "31-misc", "31-polkas", "31-reels", "31-slides"],
    ),
    Collection(
        key="levey",
        title="Levey Collection",
        folder="33",
        subfolders=["33-hps", "33-jigs", "33-marches", "33-reels", "33-sjigs"],
    ),
    Collection(
        key="ofpc",
        title="O'Farrell's Pocket Companion",
        folder="48",
        subfolders=[
            "48-hps",
            "48-jigs",
            "48-marches",
            "48-misc",
            "48-polkas",
            "48-reels",
            "48-sjigs",
        ],
    ),
    Collection(
        key="moi",
        title="Music of Ireland",
        folder="49",
        subfolders=[
            "491-airs",
            "492-hps",
            "493-jigs",
            "494-misc",
            "495-reels",
            "496-sjigs",
            "497-arr",
        ],
    ),
    Collection(
        key="roche",
        title="Roche Collection",
        folder="53",
        subfolders=["53-hps", "53-jigs", "53-misc", "53-polkas", "53-reels", "53-sjigs"],
    ),
]

_KEY_TO_COLLECTION = {c.key: c for c in COLLECTIONS}


def get_collection(key: str) -> Collection:
    """Get a collection by key."""
    try:
        return _KEY_TO_COLLECTION[key]
    except KeyError as e:
        raise ValueError(
            f"Unknown collection key: {key!r}. "
            f"Valid keys are: {sorted(c.key for c in COLLECTIONS)}."
        ) from e


def download(key: str | Iterable[str] | None = None) -> None:
    import gzip

    import requests

    SAVE_TO.mkdir(exist_ok=True)

    if key is None:  # pragma: no cover
        collections = COLLECTIONS
    elif isinstance(key, str):
        collections = [get_collection(key)]
    else:  # pragma: no cover
        collections = [get_collection(k) for k in key]

    for collection in collections:
        for url in collection.abc_urls:
            p = collection.url_to_file(url)
            logger.info(f"Downloading {url} to {p.relative_to(HERE).as_posix()}")
            r = requests.get(url, headers={"User-Agent": "pyabc2"}, timeout=5)
            r.raise_for_status()

            # Extract filename from URL and append .gz
            with gzip.open(p, "wb") as f:
                f.write(r.content)


def load_meta(key: str, *, redownload: bool = False, debug: bool = False) -> list[str]:
    """Load the tunebook data, no parsing."""
    import gzip
    import re

    if debug:  # pragma: no cover
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.NOTSET)

    collection = get_collection(key)
    if redownload or any(not p.is_file() for p in collection.files):
        print("downloading...", end=" ", flush=True)
        download(key=collection.key)
        print("done")

    abcs = []
    for p in collection.files:
        print(p)
        with gzip.open(p, "rt") as f:
            text = f.read()

        # Replace \\\n with just \n
        text = text.replace("\\\n", "\n")

        # Continuation
        text = text.replace("\\\\", "\\")

        # A tune block starts with the X: line and ends with a %%% line
        # or the end of the file.

        # Find the start of the first tune, in order to skip header info
        start = text.find("X:")
        if start == -1:  # pragma: no cover
            raise RuntimeError(f"Could not find start of tune in {p.name}")

        # Split on 3 or more %
        blocks = re.split(r"\s*%{3,}\s*", text[start:])
        if not blocks:  # pragma: no cover
            raise RuntimeError(f"Splitting blocks failed for {p.name}")

        good_blocks = []
        for i, block in enumerate(blocks):
            if not block.strip():
                logger.debug(f"Empty block {i} in {p.name}")
                continue

            if re.fullmatch(r"[0-9]+ deleted", block) is not None:
                logger.debug(f"Tune in block {i} in {p.name} marked as deleted: {block!r}")
                continue

            if not block.startswith("X:"):
                logger.debug(f"Block {i} in {p.name} does not start with `X:`: {block!r}")
                continue

            # Remove anything that may be after the final bar symbol
            j = max(block.rfind("]"), block.rfind("|"))
            assert j != -1
            good_blocks.append(block[: j + 1])
            if j < len(block) - 1:
                logger.info(
                    f"Block {i} in {p.name} has trailing data after the final bar symbol "
                    f"that will be ignored: {block[j+1:]!r}"
                )

        abcs.extend(good_blocks)

    return abcs


if __name__ == "__main__":  # pragma: no cover
    abcs = load_meta("aif", debug=True)
    print()
    print(abcs[0])
