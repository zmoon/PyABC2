"""
Notes.
Pitch class (e.g., C), Pitch (e.g., C4), Note (pitch + duration), ...
"""
# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
import functools
import re
import warnings
from typing import Dict


def _gen_pitch_values() -> Dict[str, int]:
    pitch_values = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    accidental_values = {"": 0, "#": 1, "b": -1}
    for n, v in list(pitch_values.items()):
        for a in "#b":
            pitch_values[n + a] = v + accidental_values[a]

    return pitch_values


PITCH_VALUES_WRT_C = _gen_pitch_values()
"""Dict. mapping ASCII note names ("pitch classes") to their integer values
(in the chromatic scale) with respect to C."""

ACCIDENTAL_DVALUES = {"": 0, "#": 1, "b": -1}
"""Change in value associated with a certain accidental mark (`#` or `b`)."""

CHROMATIC_NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
"""ASCII chromatic notes, starting with C at index 0."""

# https://en.wikipedia.org/wiki/Solf%C3%A8ge#Movable_do_solf%C3%A8ge
CHROMATIC_SOLFEGE = ["Do", "Di", "Re", "Me", "Mi", "Fa", "Fi", "Sol", "Le", "La", "Te", "Ti"]

CHROMATIC_SCALE_DEGREE = ["1", "1+", "2", "3-", "3", "4", "4+", "5", "6-", "6", "7-", "7"]

CHROMATIC_VALUES_IN_MAJOR = {0, 2, 4, 5, 7, 9, 11}
# TODO: for any mode


_re_pitch = re.compile(r"(?P<note>[A-G])(?P<acc>\#|b)?\s*(?P<oct>\d+)?")


def pitch_value(pitch: str, root: str = "C", *, mod: bool = False) -> int:
    """Convert a pitch string like 'A#' (note name / pitch class)
    to a chromatic scale value relative to root.
    """
    pitch = pitch.strip()

    # Base value
    val = PITCH_VALUES_WRT_C[pitch[0].upper()]

    # Add any number of accidentals
    for acc in pitch[1:]:
        val += ACCIDENTAL_DVALUES[acc]

    # Relative to root
    if root != "C":
        val -= pitch_value(root)

    # Mod? (keep in 0--11)
    if mod:
        val %= 12

    if not 0 <= val < 12:  # e.g., Cb, B##
        warnings.warn("computed pitch value outside 0--11")

    return val


# TODO: maybe a simplier PitchClass without root that PitchClass and Pitch could both inherit from


class PitchClass:
    """Pitch without octave specified."""

    def __init__(self, name: str, *, root: str = "C"):
        """
        Parameters
        ----------
        name
            Note name (ASCII).
        root
            The note set to have value=0 (normally C, which is the default).
            The root determines what value this pitch class has.
        """
        self.value = pitch_value(name, root=root, mod=True)
        """Pitch class value, as integer chromatic distance from the root (0--11)."""

        self.name = name
        """The note (pitch class) name."""

        self.root = root
        """The name of the root note (pitch class)."""

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(name='{self.name}', value={self.value}, root='{self.root}')"
        )

    @classmethod
    def from_pitch(cls, p: "Pitch") -> "PitchClass":
        return cls(p.name)

    @classmethod
    def from_value(cls, v: int, *, root: str = "C") -> "PitchClass":
        # TOOD: maybe makes more sense to have value in __init__ intead and have a from_name?
        vr = PITCH_VALUES_WRT_C[root]
        v0 = v + vr
        name0 = CHROMATIC_NOTES[v0 % 12]

        return cls(name0, root=root)

    @property
    def solfege(self) -> str:
        """Solfege symbol. Accidentals allowed."""
        return CHROMATIC_SOLFEGE[self.value]

    @property
    def scale_degree(self) -> int:
        """Scale degree within the root's Ionian scale."""
        if self.value not in CHROMATIC_VALUES_IN_MAJOR:
            raise Exception(f"{self} is not in {self.root}'s major scale")

        return int(CHROMATIC_SCALE_DEGREE[self.value])

    @property
    def scale_degree_chromatic(self) -> str:
        """Raised/lowered scale degrees expressed with +/-."""
        # TODO: roman numeral options, with leading #/b
        return CHROMATIC_SCALE_DEGREE[self.value]

    @property
    def equivalent_sharp(self) -> "PitchClass":
        pnew = self - 1
        if len(pnew.name) == 1:
            return PitchClass(pnew.name + "#", root=self.root)
        else:
            pnew = self - 2
            return PitchClass(pnew.name + "##", root=self.root)

    @property
    def equivalent_flat(self) -> "PitchClass":
        pnew = self + 1
        if len(pnew.name) == 1:
            return PitchClass(pnew.name + "b", root=self.root)
        else:
            pnew = self + 2
            return PitchClass(pnew.name + "bb", root=self.root)

    def with_root(self, root: str) -> "PitchClass":
        """New root."""
        v = self.value
        vr = PITCH_VALUES_WRT_C[self.root]
        vrnew = PITCH_VALUES_WRT_C[root]
        return PitchClass.from_value((v + vr - vrnew) % 12, root=root)

    def to_pitch(self, octave: int) -> "Pitch":
        return Pitch(self.with_root("C").value, octave)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.value == other.with_root(self.root).value

    def __add__(self, x):
        if isinstance(x, int):
            return PitchClass.from_value(self.value + x, root=self.root)
        elif isinstance(x, PitchClass):
            vnew = self.value + x.with_root(self.root).value
            return PitchClass.from_value(vnew, root=self.root)
        else:
            return NotImplemented

    def __mul__(self, x):
        if not isinstance(x, int):
            return NotImplemented

        return PitchClass.from_value(x * self.value, root=self.root)

    def __rmul__(self, x):
        return self * x

    def __neg__(self):
        return -1 * self

    def __sub__(self, x):
        return self + -x


@functools.total_ordering
class Pitch:
    """A note value relative to C, possibly with octave specified."""

    # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L204-L293
    def __init__(self, value: int, octave: int):
        """
        Parameters
        ----------
        value
            Relative note value in a C chromatic scale.
        octave
            Octave. By default octave is treated as unspecified.
        """

        doctave, value = divmod(value, 12)

        self.value = value
        """Chromatic note value relative to C"""

        self.octave = octave + doctave
        """Octave number (e.g., A 440 is in octave 4)."""

        self.name = CHROMATIC_NOTES[self.value]
        """Note name (pitch class)."""

    def __str__(self):
        return f"{self.name}{self.octave}"

    def __repr__(self):
        return f"Pitch(name='{self.name}', value={self.value}, octave={self.octave})"

    @property
    def abs_value(self):
        """Value relative to C0."""
        return self.value + self.octave * 12

    @property
    def equal_temperament_frequency(self) -> float:
        """Piano key frequency.

        https://en.wikipedia.org/wiki/Piano_key_frequencies
        """
        if self.octave is None:
            raise Exception("cannot determine frequency without a specified octave")

        n = self.octave * 12 - 8 + self.value  # C4 (middle C) is 40
        return 440 * 2 ** ((n - 49) / 12)

    @property
    def etf(self) -> float:
        """Alias for equal_temperament_frequency."""
        return self.equal_temperament_frequency

    @classmethod
    def from_etf(cls, f: float) -> "Pitch":
        from math import log2

        n_f = 12 * log2(f / 440) + 49  # piano key number

        n = int(round(n_f))  # closest integer piano key number
        e = n_f - n
        if abs(e) > 0.01:
            warnings.warn(
                f"more than one cent off ({e * 100:.2f}). "
                f"Rounding {'up' if e < 0 else 'down'} "
                f"to the nearest integer piano key."
            )

        o, v = divmod(n + 8, 12)

        return cls(value=v, octave=o)

    @classmethod
    def from_name(cls, name: str) -> "Pitch":
        m = _re_pitch.match(name)
        if m is None:
            raise ValueError(f"invalid pitch name '{name}'")

        d = m.groupdict()
        base_note_name = d["note"]
        acc = d["acc"] if d["acc"] is not None else ""
        octave = int(d["oct"])

        name = f"{base_note_name}{acc}"
        value = PITCH_VALUES_WRT_C[name]

        return cls(value, octave)

    def to_pitch_class(self, *, root: str = "C") -> PitchClass:
        return PitchClass(self.name, root=root)

    def __eq__(self, other):
        # Only for other Pitch instances
        if not isinstance(other, Pitch):
            return NotImplemented

        return self.abs_value == other.abs_value

    def __lt__(self, other):
        # Only for other Pitch instances
        if not isinstance(other, Pitch):
            return NotImplemented

        return self.abs_value < other.abs_value

    def __add__(self, x):
        if isinstance(x, int):
            doctave, dvalue = divmod(self.value + x, 12)
            return Pitch(self.value + dvalue, self.octave + doctave)
        elif isinstance(x, Pitch):
            # Adding chromatic-value-wise, not frequency-wise!
            return Pitch(self.value + x.value, self.octave + x.octave)
        else:
            return NotImplemented

    def __mul__(self, x):
        if not isinstance(x, int):
            return NotImplemented

        return Pitch(x * self.abs_value, octave=0)

    def __rmul__(self, x):
        return self * x

    def __neg__(self):
        return -1 * self

    def __sub__(self, x):
        return self + -x