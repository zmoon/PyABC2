"""
Bill Black's Irish Traditional Tune Library

https://www.capeirish.com/ittl/

Requires:

* `requests <https://requests.readthedocs.io/>`__
"""

from __future__ import annotations

import functools
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from pyabc2._util import get_logger as _get_logger

if TYPE_CHECKING:  # pragma: no cover
    import requests

logger = _get_logger(__name__)

HERE = Path(__file__).parent

SAVE_TO = HERE / "_bill-black"
TXT_RELATIVE_PATHS = [
    Path("A-tunes/A-all-ABC.txt"),
    Path("B-tunes/B-all-ABC.txt"),
    Path("C-tunes/C-all-ABC.txt"),
    Path("D-tunes/D-all-ABC.txt"),
    Path("E-tunes/E-all-ABC.txt"),
    Path("F-tunes/F-all-ABC.txt"),
    Path("G-tunes/G-all-ABC.txt"),
    Path("H-tunes/H-all-ABC.txt"),
    Path("I-tunes/I-all-ABC.txt"),
    Path("J-tunes/J-all-ABC.txt"),
    Path("K-tunes/K-all-ABC.txt"),
    Path("L-tunes/L-all-ABC.txt"),
    Path("M-tunes/M-all-ABC.txt"),
    Path("N-tunes/N-all-ABC.txt"),
    Path("O-tunes/O-all-ABC.txt"),
    Path("PQ-tunes/PQ-all-ABC.txt"),
    Path("R-tunes/R-all-ABC.txt"),
    Path("S-tunes/S-all-ABC.txt"),
    Path("T-tunes/T-all-abc.txt"),
    Path("UV-tunes/UV-all-abc.txt"),
    Path("WZ-tunes/W_Z-all-abc.txt"),
]


@functools.lru_cache(1)
def _get_session() -> requests.Session:
    return _build_session()


def _build_session() -> requests.Session:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util import Retry

    session = requests.Session()
    session.headers.update({"User-Agent": "pyabc2"})
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        backoff_jitter=0.5,
        allowed_methods={"GET", "HEAD"},
        status_forcelist=[403, 429, 500, 502, 503, 504],
        # Bill Black seems to sporadically return 403 (forbidden)
        # possibly to indicate a temporary server issue or throttling/anti-bot
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    return session


def download() -> None:
    """Download the alphabetical text files from https://www.capeirish.com/ittl/alltunes/
    and store them in a compressed archive.
    """
    import threading
    import zipfile
    from concurrent.futures import ThreadPoolExecutor

    thread_local = threading.local()

    def get_worker_session() -> requests.Session:
        # One Session per worker thread to avoid cross-thread Session sharing.
        try:
            return thread_local.session
        except AttributeError:
            session = _build_session()
            thread_local.session = session
            return session

    def download_one(url):
        session = get_worker_session()
        r = session.get(url, timeout=5)
        r.raise_for_status()
        return r.text

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for p in TXT_RELATIVE_PATHS:
            url = f"https://www.capeirish.com/ittl/alltunes/{p.as_posix()}"
            futures.append(executor.submit(download_one, url))

    SAVE_TO.mkdir(exist_ok=True)

    with zipfile.ZipFile(
        SAVE_TO / "bill_black_alltunes_text.zip",
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        for p, future in zip(TXT_RELATIVE_PATHS, futures, strict=True):
            text = future.result()
            zf.writestr(p.name, text)


def load_meta(*, redownload: bool = False, debug: bool = False) -> list[str]:
    """Load all data, splitting into ABC tune blocks and removing lines that start with ``%``.

    Parameters
    ----------
    redownload
        Re-download the data file.
    debug
        Show debug messages.

    See Also
    --------
    :doc:`/examples/sources`
    """
    import zipfile
    from collections import Counter
    from textwrap import indent

    if debug:  # pragma: no cover
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.NOTSET)

    zip_path = SAVE_TO / "bill_black_alltunes_text.zip"
    if redownload or not zip_path.is_file():
        print("downloading...", end=" ", flush=True)
        download()
        print("done")

    abcs = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for zi in zf.filelist:
            fn = zi.filename
            logger.debug(f"Loading {fn!r}")
            with zf.open(zi, "r") as f:
                text = f.read().decode("utf-8")

            # A tune block starts with the X: line and ends with a blank line
            # or the end of the file.
            # Unlike the RTF files, %%% is not _necessarily_ present as a tune separator.

            # Remove all lines that start with %
            text = "\n".join(
                line.strip() for line in text.splitlines() if not line.lstrip().startswith("%")
            )

            # For RTF, remove trailing backslashes
            if fn.endswith(".rtf"):
                text = "\n".join(line.rstrip("\\") for line in text.splitlines()).rstrip("}")

            # Find the start of the first tune, in order to skip header info
            start = text.find("X:")
            if start == -1:  # pragma: no cover
                raise RuntimeError(f"Unable to find first tune in Bill Black file {fn!r}")

            text = text[start:]

            # Separate some two-tune blocks
            # These X vals have a tune above them without an empty line in between
            if fn.startswith("c-tunes"):
                to_sep = [253, 666]
            elif fn.startswith("d-tunes"):
                to_sep = [223]
            elif fn.startswith("e-tunes"):
                to_sep = [34]
            else:
                to_sep = []
            for n in to_sep:
                text = text.replace(f"X:{n}", f"\nX:{n}")

            expected_num = text.count("X:")

            blocks = re.split(r"\n{2,}", text.rstrip())
            this_abcs = []
            for block in blocks:
                block = block.strip()
                if not block:  # pragma: no cover
                    continue

                if block.startswith(":313\nT:GRAVEL WALK (reel) (1), The"):
                    block = "X" + block
                    expected_num += 1

                if not block.startswith("X:"):
                    # First look for tune later in the block
                    # Some blocks start with comment text, sometimes including other settings but without `X:`
                    start = block.find("X:")
                    if start != -1:
                        block = block[start:]
                    else:
                        logger.info(f"skipping non-tune block in {fn!r}:\n{indent(block, '| ')}")
                        continue

                if block.count("X:") > 1:  # pragma: no cover
                    logger.warning(f"multiple X: lines in block in {fn!r}:\n{indent(block, '| ')}")

                this_abcs.append(block)

            actual_num = len(this_abcs)
            if actual_num != expected_num:  # pragma: no cover
                logger.warning(f"expected {expected_num} tunes in {fn!r}, but found {actual_num}")

            # Drop fully duplicate tune blocks while preserving order
            seen = set()
            this_abcs_unique = []
            for block in this_abcs:
                if block not in seen:
                    seen.add(block)
                    this_abcs_unique.append(block)
            if len(this_abcs_unique) < len(this_abcs):
                logger.info(
                    f"removed {len(this_abcs) - len(this_abcs_unique)}/{len(this_abcs)} fully duplicate "
                    f"tune blocks in {fn!r}"
                )
            this_abcs = this_abcs_unique

            x_counts = Counter(block.splitlines()[0] for block in this_abcs)
            x_count_counts = Counter(x_counts.values())
            if set(x_count_counts) != {1}:
                s_counts = ", ".join(f"{m} ({n})" for m, n in sorted(x_count_counts.items()))
                logger.info(f"non-unique X vals in {fn!r}: {s_counts}")

            abcs.extend(this_abcs)

    return abcs


if __name__ == "__main__":  # pragma: no cover
    tunes = load_meta(debug=True)
    print()
    print(tunes[0])
