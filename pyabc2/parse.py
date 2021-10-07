"""
ABC parsing/info
"""
import re
from typing import Dict, Iterator, List, NamedTuple, Optional

from .key import Key
from .note import _RE_NOTE, Note


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


_ABCJS_VERSION = "6.0.0-beta.33"

_fmt_abcjs_complete_page = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>{title:s}</title>
    <script src="https://cdn.jsdelivr.net/npm/abcjs@{abcjs_version:s}/dist/abcjs-basic-min.js"></script>
  </head>
  <body>
    <div id="notation"></div>

    <script>
      const tune = "{abc:s}";
      const params = {{}};
      ABCJS.renderAbc("notation", tune, params);
    </script>
  </body>
</html>
""".lstrip()

# <script src="https://cdn.jsdelivr.net/npm/abcjs@{abcjs_version:s}/dist/abcjs-basic-min.js"></script>
_fmt_abcjs = """
<div id="notation-{notation_id:s}">hi</div>

<script>
  const tune = "{abc:s}";
  const params = {{}};
  ABCJS.renderAbc("notation-{notation_id:s}", tune, params);
</script>

<script>
  const tune = "{abc:s}";
  const params = {{}};
  ABCJS.renderAbc("notation-{notation_id:s}", tune, params);
</script>
""".lstrip()

_fmt_abcjs2 = """
const tune = "{abc:s}";
const params = {{}};
ABCJS.renderAbc("notation-{notation_id:s}", tune, params);
""".lstrip()

_fmt_abcjs_load = """
<script src="https://cdn.jsdelivr.net/npm/abcjs@{abcjs_version:s}/dist/abcjs-basic-min.js"></script>
"""


def load_abcjs() -> None:
    """Load abcjs into Jupyter from CDN using IPython display."""
    from IPython.display import HTML, display  # type: ignore

    html = HTML(_fmt_abcjs_load.format(abcjs_version=_ABCJS_VERSION))
    display(html)


def _in_jupyter() -> bool:
    try:
        from IPython.core import getipython  # type: ignore
    except (ImportError, ModuleNotFoundError):
        return False

    # <class 'ipykernel.zmqshell.ZMQInteractiveShell'>
    return "zmqshell" in str(type(getipython.get_ipython()))


def _load_abcjs_if_in_jupyter() -> None:
    if _in_jupyter():
        load_abcjs()
        print("abcjs loaded")


# TODO: maybe should go in a tune module
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

        self.title: Optional[str]
        """Tune primary title (first in the ABC)."""

        self.titles: List[str]
        """All tune titles."""

        self.type: str
        """Tune type/rhythm."""

        self.key: Key
        """Key object corresponding to the tune's key."""

        self.url: Optional[str] = None
        """Revelant URL for this particular tune/setting."""

        self.measures: List[List[Note]]

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
                    if line[0] == "K":  # is K always last??
                        in_tune = True
                elif line[:2] == "+:":
                    header_lines[-1] += " " + line[2:]

        self._parse_abc_header_lines(header_lines)
        self._extract_measures(tune_lines)

    def _parse_abc_header_lines(self, header_lines: List[str]) -> None:
        h: Dict[str, str] = {}
        for line in header_lines:
            key = line[0]
            data = line[2:].strip()
            field_name = INFO_FIELDS[key].name
            n_field = sum(field_name in k for k in h.keys())
            if n_field == 0:
                h[field_name] = data
            else:
                h[f"{field_name} {n_field+1}"] = data

        self.header = h
        self.title = h.get("tune title", None)
        self.titles = [v for k, v in h.items() if "tune title" in k]
        self.type = h.get("rhythm", "?")  # TODO: guess from L/M ?
        self.key = Key(h.get("key", "C"))

    def _extract_measures(self, tune_lines: List[str]) -> None:
        # 0. Lines
        i_measure = i_measure_repeat = i_ending = 0
        measures = []
        for line in tune_lines:

            if line.startswith("|:"):
                # Left repeat detected -- new starting measure for a repeated section
                i_measure_repeat = i_measure

            # 1. In line, find measures
            for m_measure in re.finditer(r"([^\|\:\]]+)(\:?\|+\:?)", line):
                within_measure, right_sep = m_measure.groups()

                if right_sep.endswith(":"):
                    # Left repeat detected within line
                    i_measure_repeat = i_measure + 1

                if within_measure.startswith(("1", "[1", " [1")):
                    i_ending = i_measure

                if within_measure.startswith(("3", "[3", " [3")):
                    raise ValueError("3 or more endings not currently supported")

                # TODO: check for inline meter change; validate measure beat count?

                measure = []

                # 2. In measure, find note groups
                # Currently not doing anything with note group, but may want to in the future
                for note_group in within_measure.split(" "):

                    # TODO: deal with `>` and `<` dotted rhythm modifiers between notes
                    # https://abcnotation.com/wiki/abc:standard:v2.1#broken_rhythm

                    # 3. In note group, find notes
                    for m_note in _RE_NOTE.finditer(note_group):

                        # TODO: parse/store rests, maybe have an additional iterator for "rhythmic elements" or something

                        if m_note is None:
                            raise ValueError(f"no notes in this note group? {note_group!r}")

                        measure.append(Note._from_abc_match(m_note))

                measures.append(measure)

                if right_sep.startswith(":"):
                    # Right repeat detected -- extend tune from the last left repeat
                    if i_ending:
                        repeated = measures[i_measure_repeat:i_ending]
                        i_ending = 0  # reset
                    else:
                        repeated = measures[i_measure_repeat:]
                    measures.extend(repeated)
                    i_measure += len(repeated)

                i_measure += 1

        self.measures = measures

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(title={self.title!r}, key={self.key}, type={self.type!r})"
        )

    def _repr_html_(self):
        import uuid

        notation_id = str(uuid.uuid4())
        abc = "\\n".join(line for line in self.abc.strip().splitlines())

        # return _fmt_abcjs.format(abc=abc, notation_id=notation_id, abcjs_version=_ABCJS_VERSION)

        # It seems that if I just return <script> within the HTML,
        # it is never loaded.
        # https://discourse.jupyter.org/t/running-javascript-in-a-html-cell-fails-on-first-load/6707/3
        # But we can use IPython display to make it work.

        from IPython.display import HTML, Javascript, display

        html = HTML(f"<div id=notation-{notation_id}>hi</div>")
        display(html)

        js = Javascript(_fmt_abcjs2.format(abc=abc, notation_id=notation_id))
        display(js)

    def print_measures(self, *, note_format: str = "ABC"):
        """Print measures to check parsing."""
        nd = len(str(len(self.measures)))
        for i, measure in enumerate(self.measures, start=1):
            if note_format == "ABC":
                print(f"{i:0{nd}d}: {' '.join(n.to_abc(key=self.key) for n in measure)}")
            else:
                raise ValueError(f"invalid note format {note_format!r}")

    def iter_notes(self) -> Iterator[Note]:
        """Iterator (generator) for `Note`s of the tune."""
        return (n for m in self.measures for n in m)
