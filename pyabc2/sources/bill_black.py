"""
Bill Black's Irish Traditional Tune Library

http://www.capeirish.com/ittl/
"""

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
    "s-tunes-1.txt",
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


if __name__ == "__main__":  # pragma: no cover
    download()
