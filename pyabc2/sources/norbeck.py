"""
Henrik Norbeck's ABC Tunes

https://www.norbeck.nu/abc/
"""
from pathlib import Path
from typing import List, Union

# from ..parse import Tune

HERE = Path(__file__).parent

SAVE_TO = HERE / "_norbeck"


def download():
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


_TYPE_PREF = {
    "reels": "hnr",
    "jigs": "hnj",
}
# TODO: add more of the types


def _maybe_download():
    if not list(SAVE_TO.glob("*.abc")):
        print("downloading missing files...")
        download()


def load(which: Union[str, List[str]] = "all"):
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

    # def load_one_file(fp: Path):

    if which == ["all"]:

        fps = SAVE_TO.glob("*.abc")

    else:
        for tune_type in which:

            if tune_type not in _TYPE_PREF:
                raise ValueError(
                    f"tune type {tune_type!r} invalid or not supported. "
                    f"Try one of: {', '.join(repr(s) for s in _TYPE_PREF)}."
                )

            fps = SAVE_TO.glob(f"{_TYPE_PREF[tune_type]}*.abc")

            for fp in fps:
                print(fp)
