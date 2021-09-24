"""
ABC parsing/info
"""
import re
from typing import Dict, List, NamedTuple

from .key import Key


class InfoField(NamedTuple):
    # TODO: not sure of the best name for this class
    # http://abcnotation.com/wiki/abc:standard:v2.1#information_fields

    key: str
    """Field key. Single-letter identifier."""

    name: str
    """Field name."""

    allowed_in_file_header: bool
    allowed_in_tune_header: bool
    allowed_in_tune_body: bool
    allowed_in_tune_inline: bool

    type: str
    """Data type. `string`, `instruction`, or `-`."""


def _bool_yn(s: str) -> bool:
    s = s.lower()
    assert s in ("yes", "no")
    return s == "yes"


def _gen_info_field_table() -> Dict[str, InfoField]:
    raw = """
Field name          file header  tune header  tune body  inline  type
A:area              yes          yes          no         no      string
B:book              yes          yes          no         no      string
C:composer          yes          yes          no         no      string
D:discography       yes          yes          no         no      string
F:file url          yes          yes          no         no      string
G:group             yes          yes          no         no      string
H:history           yes          yes          no         no      string
I:instruction       yes          yes          yes        yes     instruction
K:key               no           yes          yes        yes     instruction
L:unit note length  yes          yes          yes        yes     instruction
M:meter             yes          yes          yes        yes     instruction
m:macro             yes          yes          yes        yes     instruction
N:notes             yes          yes          yes        yes     string
O:origin            yes          yes          no         no      string
P:parts             no           yes          yes        yes     instruction
Q:tempo             no           yes          yes        yes     instruction
R:rhythm            yes          yes          yes        yes     string
r:remark            yes          yes          yes        yes     -
S:source            yes          yes          no         no      string
s:symbol line       no           no           yes        no      instruction
T:tune title        no           yes          yes        no      string
U:user defined      yes          yes          yes        yes     instruction
V:voice             no           yes          yes        yes     instruction
W:words             no           yes          yes        no      string
w:words             no           no           yes        no      string
X:reference number  no           yes          no         no      instruction
Z:transcription     yes          yes          no         no      string
    """.strip()

    info_field_keys = {}
    for line in raw.split("\n")[1:]:
        key = line[0]
        # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L85
        m = re.match(r"(.+)\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+(.+)", line[2:])
        if m is not None:
            fields = m.groups()
        else:
            raise Exception("issue parsing the info field table")
        info_field_keys[key] = InfoField(
            key,
            fields[0].strip(),
            _bool_yn(fields[1]),
            _bool_yn(fields[2]),
            _bool_yn(fields[3]),
            _bool_yn(fields[4]),
            fields[5].strip(),
        )

    return info_field_keys


INFO_FIELDS = _gen_info_field_table()
"""Dict. mapping single-letter field keys to field info."""

FILE_HEADER_FIELD_KEYS = {k for k, v in INFO_FIELDS.items() if v.allowed_in_file_header}
TUNE_HEADER_FIELD_KEYS = {k for k, v in INFO_FIELDS.items() if v.allowed_in_tune_header}
TUNE_BODY_FIELD_KEYS = {k for k, v in INFO_FIELDS.items() if v.allowed_in_tune_body}
TUNE_INLINE_FIELD_KEYS = {k for k, v in INFO_FIELDS.items() if v.allowed_in_tune_inline}


class Tune:
    """Tune."""

    def __init__(self, abc: str):
        """
        Parameters
        ----------
        abc
            String of a single ABC tune.
        """
        self.abc = abc
        """Original ABC string."""

        self.header: Dict[str, str]
        """Information contained in the tune header."""

        self.title: str
        """Tune title."""

        self.type: str
        """Tune type/rhythm."""

        self.key: Key
        """Key object corresponding to the tune's key."""

        self._parse_abc()

    def _parse_abc(self) -> None:
        # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L520
        header_lines = []
        tune_lines = []
        in_tune = False
        for line in self.abc.split("\n"):
            line = re.split(r"([^\\]|^)%", line)[0]
            line = line.strip()
            if line == "":
                continue
            if in_tune:
                tune_lines.append(line)
            else:
                if line[0] in INFO_FIELDS and line[1] == ":":
                    header_lines.append(line)
                    if line[0] == "K":
                        in_tune = True
                elif line[:2] == "+:":
                    header_lines[-1] += " " + line[2:]

        self._parse_abc_header_lines(header_lines)

    def _parse_abc_header_lines(self, header_lines: List[str]) -> None:
        h = {}
        for line in header_lines:
            key = line[0]
            data = line[2:].strip()
            field_name = INFO_FIELDS[key].name
            h[field_name] = data

        self.header = h
        self.title = h["tune title"]
        self.type = h["rhythm"]
        self.key = Key(h["key"])

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(title={self.title!r}, key={self.key}, type={self.type!r})"
        )


if __name__ == "__main__":
    for k, info in INFO_FIELDS.items():
        if k == "G":
            break
        print(f"{k} => {info}")

    print(TUNE_INLINE_FIELD_KEYS)
