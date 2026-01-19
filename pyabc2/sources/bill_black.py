"""
Bill Black's Irish Traditional Tune Library

http://www.capeirish.com/ittl/
"""

import re
from pathlib import Path

HERE = Path(__file__).parent

SAVE_TO = HERE / "_bill-black"
TXT_FNS = [
    "a-tunes-1.txt",
    "b-tunes-1.txt",
    "c-tunes-1.txt",
    "d-tunes-1.txt",
    "e-tunes-1.txt",
    "f-tunes-1.txt",
    "g-tunes-1.txt",
    "h-tunes-1.txt",
    "i-tunes-1.txt",
    "j-tunes-1.txt",
    "k-tunes-1.txt",
    "l-tunes-1.txt",
    "m-tunes-1.txt",
    "n-tunes-1.txt",
    "o-tunes-1.txt",
    "pq-tunes-1.txt",
    "r-tunes-1.txt",
    "s-tunes-2.txt",
    "t-tunes-1.txt",
    "uv-tunes-1.txt",
    "wz-tunes-1.txt",
]


def download() -> None:
    """Download the alphabetical text files from http://www.capeirish.com/ittl/alltunes/text/
    and store them in a compressed archive.
    """
    import zipfile
    from concurrent.futures import ThreadPoolExecutor

    import requests

    def download_one(url):
        r = requests.get(url, headers={"User-Agent": "pyabc2"}, timeout=5)
        r.raise_for_status()
        return r.text

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for fn in TXT_FNS:
            url = f"http://www.capeirish.com/ittl/alltunes/text/{fn}"
            futures.append(executor.submit(download_one, url))

    SAVE_TO.mkdir(exist_ok=True)

    with zipfile.ZipFile(
        SAVE_TO / "bill_black_alltunes_text.zip",
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        for fn, future in zip(TXT_FNS, futures, strict=True):
            text = future.result()
            zf.writestr(fn, text)


def load_meta(*, redownload: bool = False) -> list[str]:
    """Load all data, splitting into tune blocks and removing ``%`` lines."""
    import zipfile
    from collections import Counter
    from textwrap import indent

    zip_path = SAVE_TO / "bill_black_alltunes_text.zip"
    if redownload or not zip_path.is_file():
        print("downloading...", end=" ", flush=True)
        download()
        print("done")

    tunes = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for zi in zf.filelist:
            fn = zi.filename
            with zf.open(zi, "r") as f:
                text = f.read().decode("utf-8")

            # A tune block starts with the X: line and ends with a blank line
            # or the end of the file.
            # Unlike the RTF files, %%% is not _necessarily_ present as a tune separator.

            # Remove all lines that start with %
            text = "\n".join(
                line.strip() for line in text.splitlines() if not line.lstrip().startswith("%")
            )

            # Find the start of the first tune, in order to skip header info
            start = text.find("X:")
            if start == -1:
                raise RuntimeError(f"Unable to find first tune in Bill Black file {fn!r}")

            text = text[start:]

            # Separate some blocks that are missing empty lines
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
            this_tunes = []
            for block in blocks:
                block = block.strip()
                if not block:
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
                        print(f"note: skipping non-tune block in {fn!r}:\n{indent(block, '| ')}")
                        continue

                if block.count("X:") > 1:
                    print(f"warning: multiple X: lines in block in {fn!r}:\n{indent(block, '| ')}")

                this_tunes.append(block)

            actual_num = len(this_tunes)
            if actual_num != expected_num:
                print(f"warning: expected {expected_num} tunes in {fn!r}, but found {actual_num}")

            # Drop fully duplicate tune blocks while preserving order
            seen = set()
            this_tunes_unique = []
            for block in this_tunes:
                if block not in seen:
                    seen.add(block)
                    this_tunes_unique.append(block)
            if len(this_tunes_unique) < len(this_tunes):
                print(
                    f"note: removed {len(this_tunes) - len(this_tunes_unique)}/{len(this_tunes)} fully duplicate "
                    f"tune blocks in {fn!r}"
                )
            this_tunes = this_tunes_unique

            x_counts = Counter(block.splitlines()[0] for block in this_tunes)
            x_count_counts = Counter(x_counts.values())
            if set(x_count_counts) != {1}:
                s_counts = ", ".join(f"{m} ({n})" for m, n in sorted(x_count_counts.items()))
                print(f"note: non-unique X vals in {fn!r}: {s_counts}")

            tunes.extend(this_tunes)

    return tunes


if __name__ == "__main__":  # pragma: no cover
    tunes = load_meta()
