"""
Load data from the Eskin tunebook websites.
"""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from pyabc2.sources._lzstring import LZString

HERE = Path(__file__).parent

SAVE_TO = HERE / "_eskin"

_TBW = "https://michaeleskin.com/tunebook_websites"
_CCE_SD = "https://michaeleskin.com/cce_sd"
_TBWS = {
    # https://michaeleskin.com/tunebooks.html#websites_irish
    "kss": f"{_TBW}/king_street_sessions_tunebook_17Jan2025.html",
    "carp": f"{_TBW}/carp_celtic_jam_tunebook_17Jan2025.html",
    "hardy": f"{_TBW}/paul_hardy_2024_8feb2025.html",
    "cce_dublin_2001": f"{_CCE_SD}/cce_dublin_2001_tunebook_17Jan2025.html",
    "cce_san_diego": f"{_CCE_SD}/cce_san_diego_tunes_31jan2025.html",
    # https://michaeleskin.com/tunebooks.html#websites_18th_century_collections
    "aird": f"{_TBW}/james_aird_campin_18jan2025.html",
    "playford1": f"{_TBW}/playford_1_partington_17jan2025.html",
    "playford2": f"{_TBW}/playford_2_partington_17jan2025.html",
    "playford3": f"{_TBW}/playford_3_partington_20jan2025.html",
}

# https://michaeleskin.com/tunebook_websites/king_street_sessions_tunebook_17Jan2025.html
# reels line extract
s = """\
    const reels=[{"Name":"An Moinfheir","URL":"https://michaeleskin.com/abctools/abctools.html?lzw=BoLgBAjAUApDAuBLeAbApgMwPYDt5gAUBDFIpHLMAJithgGcBXAIyVU132NL0QsgAcdPtmx5CJMn0oQALFAAqIAII4wAWSwiAFmkQAnKACUQRtGhRQA8iACS+i0RwATKAGUQ6xvUQBjMBj6WAC2YPaOLmAAalgoAHRgAMxQAEKe3n4BQaHhPM7RsQnJAFogCvpO9L76iAAOSLjg6ogA1mhgADK4AOZQ6iAAwlAdIBAA9EIA0iAAIrAGiPTaAPpBKCj0y7iwRMy+AFab9FiMLmL4GGTMWACedOq2M7ZgtUHdFaEADPePz8xE9Horyw3TA3zgDyeYF82iw+mcwNB4JgkL+APoADdYmAAKzI1HQ2HwrEoXHfABEM3JzioYGUAHEwAAxZRgGZUAA+ygANDMwAA-dlgZy+Bkcynk5T5fk0sCU4KSgC8GDQznFA3Jit8tPp-gAor5dRyADpQCWyhnM5QzFLcrm8gVCkViqBSgUW5ws9Xk+mKgZ6xkSpkzdkgE1QDkgc20jD5IjOS7e7pa1Vy5TkgB6opSvnFVJltLdLJmTI5Zvp5P59NpLLlGq1tJz4YlboLdITasl5N8zkwYG6Me6HP5RFpaCI0KIaFz5IAFPSAJTU0WBqm10McoA&format=noten&ssp=10&name=An_Moinfheir&play=1"},{"Name":"Around the world","URL":"https://michaeleskin.com/abctools/abctools.html?lzw=BoLgBATAUApDAuBLeAbApgMwPYDt5gAUBDFIpHLSaOAZwFcAjJVTXfY0vRCsARgA5YMbtmx5CJMt0q8ALFAAqIAIIAnLHRwATMPAAWaMAHcsqlFsUgFB44hqGAtkUQWASiFdo0KKAHkQAJKq3kTaUADKgap2emAKqkRayIi4JGAAsnQ0iADGYOFoNNm4cZqFUABCUTFxCUlIqSgZWbn5hcU4pTjlAFpWCTg0OdEADg04ADRgRKoDAOZoDmh4Uzl6plo0IOmIANaGADK4c1DpIADCUAcgvAD0ggDSIAAisIjRNHoA+uooKDRfXCwIgMHIAKwBNA02jE+AwZAYWAAnkJ0gFngEwCN1HMEg4wAAGVHozEMIhFbFYOaE4kYsBrDaU6lEuBoulkooANywTQArCyYGzMQzVFpuXyiQAiZ6SgBiEFlAHEwLKAKLPVUAH1lymUFTAyjVz010slWggYAAFABmS2YOYASjAkuUkowWjQORNMq0FUNztdFVV6s1AB0oKb5UqVeqtTq9QajWGIz6LTa7RhHQG3R6vVAANq8Z2Ks1+5WR54akCa-MWyUl33Kcsy2XPHXhzUgU3mpsqtvKb1m+EYbNzDBoOaDjDKLQjl2StDKHJoTUpodoHTznK6iDJ+uSioQRX603KfuD2dEOeuscbk0l9MVHJaJ3L52W54O0tNmtFyOu11VVlZ0ZWeBVlGrWsQLlADJVVZtpQgDVNQAXSAA&format=noten&ssp=10&name=Around_the_world&play=1"}];
""".strip().rstrip(
    ";"
)


def abctools_url_to_abc(url: str) -> str:
    """Extract the ABC from an abctools share URL."""
    res = urlsplit(url)
    assert res.netloc == "michaeleskin.com"
    assert res.path.startswith("/abctools/")

    query_params = parse_qs(res.query)
    (lzw,) = query_params["lzw"]
    # Note `+` has been replaced with space by parse_qs
    # js LZString.compressToEncodedURIComponent() is used to compress/encode the ABC

    # TODO: optionally remove the lines that start with % or at least the %% lines

    return LZString.decompressFromEncodedURIComponent(lzw)


def _download_data(tunebook_url: str):
    """Extract and save the tune data from the tunebook webpage as JSON."""
    import gzip
    import re

    import requests

    r = requests.get(tunebook_url, timeout=5)
    r.raise_for_status()
    html = r.text

    # First find the tune type options by searching for 'tunes = type;'
    types = sorted(set(re.findall(r"tunes = (.*?);", html)))
    if not types:
        raise RuntimeError("Unable to detect tune types")
    print(types)

    # Then the data are in like `const reels=[{...}, ...];`
    all_data = {}
    for type_ in types:
        m = re.search(f"const {type_}=(.*?);", html, flags=re.DOTALL)
        if m is None:
            raise RuntimeError(f"Unable to find data for type {type_!r}")
        s_data = m.group(1)

        try:
            data = json.loads(s_data)
        except json.JSONDecodeError as e:
            print(s_data[e.pos], "context:", s_data[e.pos - 10 : e.pos + 10])
            raise

        for d in data:
            assert d.keys() == {"Name", "URL"}
            d["name"] = d.pop("Name")
            d["abc"] = abctools_url_to_abc(d.pop("URL"))

        all_data[type_] = data

    SAVE_TO.mkdir(exist_ok=True)
    stem = Path(urlsplit(tunebook_url).path).stem
    with gzip.open(SAVE_TO / f"{stem}.json.gz", "wt") as f:
        json.dump(all_data, f, indent=2)


_download_data(_TBWS["kss"])
