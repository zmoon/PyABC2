"""
Load data from the Eskin tunebook websites.
"""

import json
from urllib.parse import parse_qs, urlsplit

from pyabc2.sources._lzstring import LZString

# https://michaeleskin.com/tunebook_websites/king_street_sessions_tunebook_17Jan2025.html
# reels line extract
s = """\
    const reels=[{"Name":"An Moinfheir","URL":"https://michaeleskin.com/abctools/abctools.html?lzw=BoLgBAjAUApDAuBLeAbApgMwPYDt5gAUBDFIpHLMAJithgGcBXAIyVU132NL0QsgAcdPtmx5CJMn0oQALFAAqIAII4wAWSwiAFmkQAnKACUQRtGhRQA8iACS+i0RwATKAGUQ6xvUQBjMBj6WAC2YPaOLmAAalgoAHRgAMxQAEKe3n4BQaHhPM7RsQnJAFogCvpO9L76iAAOSLjg6ogA1mhgADK4AOZQ6iAAwlAdIBAA9EIA0iAAIrAGiPTaAPpBKCj0y7iwRMy+AFab9FiMLmL4GGTMWACedOq2M7ZgtUHdFaEADPePz8xE9Horyw3TA3zgDyeYF82iw+mcwNB4JgkL+APoADdYmAAKzI1HQ2HwrEoXHfABEM3JzioYGUAHEwAAxZRgGZUAA+ygANDMwAA-dlgZy+Bkcynk5T5fk0sCU4KSgC8GDQznFA3Jit8tPp-gAor5dRyADpQCWyhnM5QzFLcrm8gVCkViqBSgUW5ws9Xk+mKgZ6xkSpkzdkgE1QDkgc20jD5IjOS7e7pa1Vy5TkgB6opSvnFVJltLdLJmTI5Zvp5P59NpLLlGq1tJz4YlboLdITasl5N8zkwYG6Me6HP5RFpaCI0KIaFz5IAFPSAJTU0WBqm10McoA&format=noten&ssp=10&name=An_Moinfheir&play=1"},{"Name":"Around the world","URL":"https://michaeleskin.com/abctools/abctools.html?lzw=BoLgBATAUApDAuBLeAbApgMwPYDt5gAUBDFIpHLSaOAZwFcAjJVTXfY0vRCsARgA5YMbtmx5CJMt0q8ALFAAqIAIIAnLHRwATMPAAWaMAHcsqlFsUgFB44hqGAtkUQWASiFdo0KKAHkQAJKq3kTaUADKgap2emAKqkRayIi4JGAAsnQ0iADGYOFoNNm4cZqFUABCUTFxCUlIqSgZWbn5hcU4pTjlAFpWCTg0OdEADg04ADRgRKoDAOZoDmh4Uzl6plo0IOmIANaGADK4c1DpIADCUAcgvAD0ggDSIAAisIjRNHoA+uooKDRfXCwIgMHIAKwBNA02jE+AwZAYWAAnkJ0gFngEwCN1HMEg4wAAGVHozEMIhFbFYOaE4kYsBrDaU6lEuBoulkooANywTQArCyYGzMQzVFpuXyiQAiZ6SgBiEFlAHEwLKAKLPVUAH1lymUFTAyjVz010slWggYAAFABmS2YOYASjAkuUkowWjQORNMq0FUNztdFVV6s1AB0oKb5UqVeqtTq9QajWGIz6LTa7RhHQG3R6vVAANq8Z2Ks1+5WR54akCa-MWyUl33Kcsy2XPHXhzUgU3mpsqtvKb1m+EYbNzDBoOaDjDKLQjl2StDKHJoTUpodoHTznK6iDJ+uSioQRX603KfuD2dEOeuscbk0l9MVHJaJ3L52W54O0tNmtFyOu11VVlZ0ZWeBVlGrWsQLlADJVVZtpQgDVNQAXSAA&format=noten&ssp=10&name=Around_the_world&play=1"}];
""".strip().rstrip(
    ";"
)

_, s = s.split(" ", 1)
type_, s = s.split("=", 1)

try:
    data = json.loads(s)
except json.JSONDecodeError as e:
    print(s[e.pos], "context:", s[e.pos - 10 : e.pos + 10])
    raise

for d in data[:1]:
    name = d["Name"]
    abctools_url = d["URL"]
    res = urlsplit(abctools_url)
    assert res.netloc == "michaeleskin.com"
    query_params = parse_qs(res.query)
    (lzw,) = query_params["lzw"]  # note `+` has been replaced with space

    # Example LZW string (made by js `LZString.compressToEncodedURIComponent()`):
    # 'BoLgBAjAUApDAuBLeAbApgMwPYDt5gAUBDFIpHLMAJithgGcBXAIyVU132NL0QsgAcdPtmx5CJMn0oQALFAAqIAII4wAWSwiAFmkQAnKACUQRtGhRQA8iACS i0RwATKAGUQ6xvUQBjMBj6WAC2YPaOLmAAalgoAHRgAMxQAEKe3n4BQaHhPM7RsQnJAFogCvpO9L76iAAOSLjg6ogA1mhgADK4AOZQ6iAAwlAdIBAA9EIA0iAAIrAGiPTaAPpBKCj0y7iwRMy AFab9FiMLmL4GGTMWACedOq2M7ZgtUHdFaEADPePz8xE9Horyw3TA3zgDyeYF82iw mcwNB4JgkL APoADdYmAAKzI1HQ2HwrEoXHfABEM3JzioYGUAHEwAAxZRgGZUAA ygANDMwAA-dlgZy Bkcynk5T5fk0sCU4KSgC8GDQznFA3Jit8tPp-gAor5dRyADpQCWyhnM5QzFLcrm8gVCkViqBSgUW5ws9Xk mKgZ6xkSpkzdkgE1QDkgc20jD5IjOS7e7pa1Vy5TkgB6opSvnFVJltLdLJmTI5Zvp5P59NpLLlGq1tJz4YlboLdITasl5N8zkwYG6Me6HP5RFpaCI0KIaFz5IAFPSAJTU0WBqm10McoA'
    text = LZString.decompressFromEncodedURIComponent(lzw)
