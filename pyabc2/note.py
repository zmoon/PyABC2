"""
Note class (pitch + duration)
"""
import re
from fractions import Fraction
from typing import Optional

from .key import Key
from .pitch import ACCIDENTAL_DVALUES, Pitch, pitch_class_value

_S_RE_NOTE = (
    r"(?P<acc>\^|\^\^|=|_|__)?"
    r"(?P<note>[a-gA-G])"
    r"(?P<oct>[,']*)"
    r"(?P<num>[0-9]+)?"
    r"(?P<slash>/+)?"
    r"(?P<den>[0-9]+)?"
)
_RE_NOTE = re.compile(_S_RE_NOTE)


_ACCIDENTAL_ASCII_TO_ABC = {"#": "^", "b": "_", "=": "="}
_ACCIDENTAL_ABC_TO_ASCII = {v: k for k, v in _ACCIDENTAL_ASCII_TO_ABC.items()}

_DURATION_FRAC_TO_HTML = {
    Fraction("1"): "&#119133;",
    Fraction("1/2"): "&#119134;",
    Fraction("1/4"): "&#119135;",
    Fraction("1/8"): "&#119136;",
    Fraction("1/16"): "&#119137;",
    Fraction("1/32"): "&#119138;",
    Fraction("1/64"): "&#119139;",
    Fraction("1/128"): "&#119140;",
}


def _octave_from_abc_parts(note: str, oct: Optional[str] = None, *, base: int = 4):
    """
    Parameters
    ----------
    base
        The octave number of the uppercase notes with no `,` or `'` (C, D, E, F, ...).
    """
    doctave_from_case = 0 if note.isupper() else 1
    if oct is not None:
        doctave_plus = oct.count("'")
        doctave_minus = oct.count(",")
    else:
        doctave_plus = doctave_minus = 0

    return base + doctave_from_case + doctave_plus - doctave_minus


_DEFAULT_OCTAVE_BASE = 4
_DEFAULT_KEY = Key("Cmaj")
_DEFAULT_UNIT_DURATION = Fraction("1/8")


class Note(Pitch):
    """A note has a pitch and a duration."""

    def __init__(self, value: int, duration: Fraction = _DEFAULT_UNIT_DURATION):

        super().__init__(value)

        self.duration = duration
        """Note duration. By default, 1/8, an eighth note."""

    def __str__(self):
        return f"{self.name}_{self.duration}"

    def __repr__(self):
        return f"{type(self).__name__}(value={self.value}, duration={self.duration})"

    def _repr_html_(self):
        p = super()._repr_html_()
        d = self.duration
        d1, nd1 = d / d.numerator, d.numerator

        if nd1 == 3 and d1 <= 0.5:
            # Go up one level and add dot
            return f"{p}{_DURATION_FRAC_TO_HTML[d1*2]}."
        elif nd1 == 1:
            return f"{p}{_DURATION_FRAC_TO_HTML[d1]}"
        else:
            # 2 or more whole notes (biggest duration)
            # or whole note(s) + additional
            # or 5 1/8 notes
            # etc.
            # TODO: ties or adding multiples
            return f"{p}({nd1}{_DURATION_FRAC_TO_HTML[d1]})"

    def __eq__(self, other):
        if not isinstance(other, Note):
            return NotImplemented

        return self.value == other.value and self.duration == other.duration

    @classmethod
    def from_abc(
        cls,
        abc: str,
        *,
        key: Key = _DEFAULT_KEY,
        octave_base: int = _DEFAULT_OCTAVE_BASE,
        unit_duration: Fraction = _DEFAULT_UNIT_DURATION,
    ):
        m = _RE_NOTE.match(abc)
        return cls._from_abc_match(m, key=key, octave_base=octave_base, unit_duration=unit_duration)

    @classmethod
    def _from_abc_match(
        cls,
        m: Optional[re.Match],
        *,
        key: Key = _DEFAULT_KEY,
        octave_base: int = _DEFAULT_OCTAVE_BASE,
        unit_duration: Fraction = _DEFAULT_UNIT_DURATION,
    ):
        # `re.Match[str]` seems to work only in 3.9+ ?
        # TODO: key could be a string or Key instance to make it simpler?
        if m is None:
            raise ValueError("invalid ABC note specification")
            # TODO: would be nice to have the input string in this error message

        g = m.groupdict()

        note = g["note"]
        octave_marks = g["oct"]
        acc_marks = g["acc"]

        octave = _octave_from_abc_parts(note, octave_marks, base=octave_base)
        nat_class_name = note.upper()

        if acc_marks is not None:
            acc_ascii = acc_marks
            for a, b in _ACCIDENTAL_ABC_TO_ASCII.items():
                acc_ascii = acc_ascii.replace(a, b)
        else:
            acc_ascii = ""

        # Compute value
        dvalue_acc = 0 if acc_marks is None else acc_marks.count("^") - acc_marks.count("_")
        if acc_marks is None:
            # Only bring in key signature if no accidental marks
            dvalue_key = (
                0
                if nat_class_name not in key.accidentals
                else ACCIDENTAL_DVALUES[key.accidentals[nat_class_name]]
            )
        else:
            dvalue_key = 0
        value = pitch_class_value(nat_class_name) + 12 * octave + dvalue_acc + dvalue_key

        # Determine duration
        sla = g["slash"]
        num = g["num"]
        den = g["den"]
        if sla is not None:
            # raise ValueError("only whole multiples of L supported at this time")
            if num is None and den is None:
                # Special case: `/` as shorthand for 1/2 and can be multiple
                relative_duration = Fraction("1/2") ** sla.count("/")
            elif num is not None and den is not None:
                # We have both numerator and denominator
                assert (
                    sla == "/"
                ), "there should only be one `/` when using both numerator and denominator"
                relative_duration = Fraction(f"{num}/{den}")
            elif den is not None:
                # When only denominator, numerator 1 is assumed
                assert sla == "/", "there should only be one `/` when only denominator is used"
                relative_duration = Fraction(f"1/{den}")
            elif num is not None:
                # When only numerator, denominator 2 is assumed
                assert sla == "/", "there should be only one `/` when only numerator is used"
                # ^ Not 100% sure about this though
                relative_duration = Fraction(f"{num}/2")
            else:
                raise ValueError(f"invalid relative duration spec. in {m.group(0)!r}")
                # (Shouldn't ever get here.)
        else:
            relative_duration = Fraction(num) if num is not None else Fraction(1)

        note = cls(value, relative_duration * unit_duration)
        note._class_name = nat_class_name + acc_ascii
        note._octave = octave

        return note

    def to_abc(
        self,
        *,
        key: Key = _DEFAULT_KEY,
        octave_base: int = _DEFAULT_OCTAVE_BASE,
        unit_duration: Fraction = _DEFAULT_UNIT_DURATION,
    ):
        octave = self.octave
        note_name = self.class_name

        # Accidental(s). Hack for now
        if len(note_name) == 1:
            note_nat = note_name
            acc = ""
        elif len(note_name) == 2:
            note_nat = note_name[0]
            acc = _ACCIDENTAL_ASCII_TO_ABC[note_name[1]]
        else:
            raise NotImplementedError(f"note name longer than 2 chars {note_name!r}")

        # Adjust for key sig
        if acc and note_nat in key.accidentals:
            acc = ""

        # Lowercase letter if in 2nd octave or more
        if octave > octave_base:
            note_nat = note_nat.lower()

        # Octave marks
        if octave < octave_base:
            octave_marks = "," * (octave_base - octave)
        elif octave in (octave_base, octave_base + 1):
            octave_marks = ""
        else:
            octave_marks = "'" * (octave - octave_base + 1)

        # Duration
        relative_duration = self.duration / unit_duration
        if relative_duration == 1:
            s_duration = ""  # relative duration 1 is implied so not needed
        elif relative_duration.numerator == 1:
            s_duration = f"/{relative_duration.denominator}"  # numerator 1 implied so not needed
        else:
            s_duration = str(relative_duration)

        return f"{acc}{note_nat}{octave_marks}{s_duration}"

    @classmethod
    def from_pitch(cls, p: Pitch, *, duration: Fraction = _DEFAULT_UNIT_DURATION) -> "Note":
        note = cls(p.value, duration)
        note._class_name = p._class_name
        note._octave = p._octave

        return note

    def to_pitch(self) -> Pitch:
        p = Pitch(self.value)
        p._class_name = self._class_name

        return p

    @classmethod
    def from_name(cls):
        raise NotImplementedError

    @classmethod
    def from_etf(cls):
        raise NotImplementedError

    @classmethod
    def from_pitch_class(cls):
        raise NotImplementedError

    @classmethod
    def from_class_name(cls):
        raise NotImplementedError

    @classmethod
    def from_class_value(cls):
        raise NotImplementedError
