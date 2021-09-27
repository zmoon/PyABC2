"""
Note class (pitch + duration)
"""
import re
from typing import Optional

from .key import Key
from .pitch import ACCIDENTAL_DVALUES, Pitch, pitch_class_value

_s_re_note = (
    r"(?P<acc>\^|\^\^|=|_|__)?"
    r"(?P<note>[a-gA-G])"
    r"(?P<oct>[,']*)"
    r"(?P<num>[0-9]+)?"
    r"(?P<slash>/+)?"
    r"(?P<den>\d+)?"
)
_re_note = re.compile(_s_re_note)

_OCTAVE_BASE_DEFAULT = 4

_ACCIDENTAL_TO_ABC = {"#": "^", "b": "_"}


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


_DEFAULT_KEY = Key("Cmaj")


class Note(Pitch):
    """A note has a pitch and a duration."""

    def __init__(self, value: int, duration: int = 1):

        super().__init__(value)

        self.duration = duration
        """Note duration, as a multiple of the base (usually one)."""

        # TODO: could use fractions.Fraction for the duration or the base (=1) duration

    def __str__(self):
        return f"{self.name}_{self.duration}"

    def __repr__(self):
        return f"{self.__class__.__name__}(value={self.value}, duration={self.duration})"

    def __eq__(self, other):
        if not isinstance(other, Note):
            return NotImplemented

        return self.value == other.value and self.duration == other.duration

    @classmethod
    def from_abc(
        cls, abc: str, *, key: Key = _DEFAULT_KEY, octave_base: int = _OCTAVE_BASE_DEFAULT
    ):
        m = _re_note.match(abc)
        return cls._from_abc_match(m, octave_base=octave_base, key=key)

    @classmethod
    def _from_abc_match(
        cls,
        m: Optional[re.Match],
        *,
        key: Key = _DEFAULT_KEY,
        octave_base: int = _OCTAVE_BASE_DEFAULT,
    ):
        # `re.Match[str]` seems to work only in 3.9+ ?
        # TOOD: key could be a string or Key instance to make it simpler?
        if m is None:
            raise ValueError("invalid ABC note specification")
            # TODO: would be nice to have the input string in this error message

        g = m.groupdict()

        note = g["note"]
        octave_marks = g["oct"]
        acc_marks = g["acc"]

        octave = _octave_from_abc_parts(note, octave_marks, base=octave_base)
        class_name = note.upper()

        # Compute value
        dvalue_acc = 0 if acc_marks is None else acc_marks.count("^") - acc_marks.count("_")
        if acc_marks is None:
            # Only bring in key signature if no accidental marks
            dvalue_key = (
                0
                if class_name not in key.accidentals
                else ACCIDENTAL_DVALUES[key.accidentals[class_name]]
            )
        else:
            dvalue_key = 0
        value = pitch_class_value(class_name) + 12 * octave + dvalue_acc + dvalue_key

        # Determine duration
        if g["slash"] is not None:
            raise ValueError("only whole multiples of L supported at this time")
        duration = int(g["num"]) if g["num"] is not None else 1

        return cls(value, duration)

    def to_abc(self, *, key: Key = _DEFAULT_KEY, octave_base: int = _OCTAVE_BASE_DEFAULT):
        octave = self.octave
        note_name = self.class_name

        # Accidental(s). Hack for now
        # TODO: add some accidental properties and stuff to PitchClass
        if len(note_name) == 1:
            note_nat = note_name
            acc = ""
        elif len(note_name) == 2:
            note_nat = note_name[0]
            acc = _ACCIDENTAL_TO_ABC[note_name[1]]
        else:
            raise NotImplementedError(r"note name longer than 2 chars {note_name!r}")

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
        duration = self.duration
        s_duration = "" if duration == 1 else str(duration)  # duration is 1 implied so not needed

        return f"{acc}{note_nat}{octave_marks}{s_duration}"

    # TODO: some other to methods
