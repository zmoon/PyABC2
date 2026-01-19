"""
Bill Black's Irish Traditional Tune Library

http://www.capeirish.com/ittl/
"""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

HERE = Path(__file__).parent

ITTL = "http://www.capeirish.com/ittl/"
SAVE_TO = HERE / "_bill-black"


@dataclass
class Collection:
    key: str
    title: str
    folder: str
    volumes: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)

    @property
    def abc_urls(self) -> list[str]:
        if self.urls:
            return self.urls
        else:
            num = self.folder
            if self.volumes:
                return [f"{ITTL}tunefolders/{num}/{vol}/{vol}-ABC.rtf" for vol in self.volumes]
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
        urls=[
            f"{ITTL}bbmg/{char}-tunes-ABC.rtf"
            for char in [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
                "I-J",
                "K",
                "L",
                "M",
                "N",
                "O",
                "P-Q",
                "R",
                "S",
                "T",
                "U-Y",
            ]
        ],
    ),
    Collection(
        key="bs",
        title="Bulmer & Sharpley",
        folder="13",
        volumes=["131", "132", "133", "134"],
    ),
    Collection(
        key="car",
        title="Carolan Tunes",
        folder="14",
    ),
    # http://www.capeirish.com/ittl/tunefolders/18/181/181-ABC.rtf
    Collection(
        key="cre",
        title="Ceol Rince na hÉireann",
        folder="18",
        volumes=["181", "182", "183", "184", "185"],
    ),
    Collection(
        key="dmi",
        title="Dance Music of Ireland",
        folder="21",
    ),
    Collection(
        key="dmwc",
        title="Dance Music of Willie Clancy",
        folder="22",
    ),
    Collection(
        key="foinn",
        title="Foinn Seisiún",
        folder="25",
        volumes=["251", "252", "253"],
    ),
    Collection(
        key="jol",
        title="Johnny O'Leary of Sliabh Luachra",
        folder="31",
    ),
    Collection(
        key="levey",
        title="Levey Collection",
        folder="33",
        volumes=["331", "332"],
    ),
    Collection(
        key="ofpc",
        title="O'Farrell's Pocket Companion",
        folder="48",
        volumes=["481", "482", "483", "484"],
    ),
    Collection(
        key="moi",
        title="Music of Ireland",
        folder="49",
        volumes=["491", "492", "493", "494", "495", "496", "497"],
    ),
    Collection(
        key="roche",
        title="Roche Collection",
        folder="53",
        volumes=["531", "532", "533", "534"],  # TODO: 535 is missing
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


def download(key: str | Iterable[str] | None = None, *, verbose: bool = False) -> None:
    import gzip

    import requests

    SAVE_TO.mkdir(exist_ok=True)

    if key is None:
        collections = COLLECTIONS
    elif isinstance(key, str):
        collections = [get_collection(key)]
    else:
        collections = [get_collection(k) for k in key]

    for collection in collections:
        for url in collection.abc_urls:
            p = collection.url_to_file(url)
            if verbose:
                print(f"Downloading {url} to {p.relative_to(HERE).as_posix()}")
            r = requests.get(url, timeout=5)
            r.raise_for_status()

            # Extract filename from URL and append .gz
            with gzip.open(p, "wb") as f:
                f.write(r.content)


def load_meta(key: str, *, redownload: bool = False) -> list[str]:
    """Load the tunebook data, no parsing."""

    import gzip
    import re

    collection = get_collection(key)
    if redownload or any(not p.is_file() for p in collection.files):
        print("downloading...", end=" ", flush=True)
        download(key=collection.key, verbose=False)
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
        if start == -1:
            raise RuntimeError(f"Could not find start of tune in {p.name}")

        # Split on 3 or more %
        blocks = re.split(r"\s*%{3,}\s*", text[start:])
        if not blocks:
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


if __name__ == "__main__":
    # download(verbose=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s:%(message)s",
    )

    abcs = load_meta("cre")
