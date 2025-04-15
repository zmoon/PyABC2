"""
Bill Black's Irish Traditional Tune Library

http://www.capeirish.com/ittl/tunefolders/
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

HERE = Path(__file__).parent

ITTL = "http://www.capeirish.com/ittl/"
SAVE_TO = HERE / "_bill-black"


@dataclass
class Collection:
    key: str
    title: str
    folder: str
    volumes: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)

    @property
    def abc_urls(self) -> List[str]:
        if self.urls:
            return self.urls
        else:
            num = self.folder
            if self.volumes:
                return [f"{ITTL}tunefolders/{num}/{vol}/{vol}-ABC.rtf" for vol in self.volumes]
            else:
                return [f"{ITTL}tunefolders/{num}/{num}-ABC.rtf"]

    @property
    def files(self) -> List[Path]:
        return [self.url_to_file(url) for url in self.abc_urls]

    def url_to_file(self, url: str) -> Path:
        """Convert a URL to a file path."""
        return SAVE_TO / f"{url.split('/')[-1]}.gz"


COLLECTIONS: List[Collection] = [
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


def download(key: Optional[Union[str, List[str]]] = None, *, verbose: bool = False) -> None:
    import gzip

    import requests

    SAVE_TO.mkdir(exist_ok=True)

    if key is None:
        collections = COLLECTIONS
    elif isinstance(key, str):
        collections = [_KEY_TO_COLLECTION[key]]
    else:
        collections = [_KEY_TO_COLLECTION[k] for k in key]

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


if __name__ == "__main__":
    download(verbose=True)
