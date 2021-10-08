"""
Pitch class (e.g., C), Pitch (e.g., C4)
"""
# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
import functools
import re
import warnings
from fractions import Fraction
from typing import Dict, Optional


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

ACCIDENTAL_DVALUES = {"": 0, "#": 1, "b": -1, "=": 0}
"""Change in value associated with a certain accidental mark (`#` or `b`)."""

_ACCIDENTAL_ASCII_TO_UNICODE = {
    "": "",
    "#": "♯",
    "b": "♭",
    "##": "𝄪",
    "bb": "𝄫",
    "=": "♮",
}
_ACCIDENTAL_ASCII_TO_PM = {
    "": "",
    "#": "+",
    "b": "-",
    "=": "=",
}
_ACCIDENTAL_ASCII_TO_HTML = {
    "": "",
    "#": "&sharp;",
    "b": "&flat;",
    "=": "&natural;",
    "bb": "&#119083;",
    "##": "&#119082;",
}

NICE_C_CHROMATIC_NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
"""ASCII chromatic notes, starting with C at index 0.
The more common accidentals are used.
"""

_S_RE_PITCH_CLASS = r"[A-G][\#b\=]*"
_RE_PITCH_CLASS = re.compile(_S_RE_PITCH_CLASS)
# _S_RE_PITCH_CLASS_ONE_ACC = r"[A-G][\#|b]?"
_RE_PITCH = re.compile(rf"(?P<pitch_class>{_S_RE_PITCH_CLASS})" r"\s*" r"(?P<octave>[0-9]+)")


def pitch_class_value(pitch: str, root: str = "C", *, mod: bool = False) -> int:
    """Convert a pitch string like 'A#' (note name / pitch class)
    to a chromatic scale value in 0--11 relative to root.
    """
    pitch = pitch.strip()

    if not _RE_PITCH_CLASS.fullmatch(pitch):
        raise ValueError(f"invalid pitch class specification '{pitch}'")

    # Base value
    val = PITCH_VALUES_WRT_C[pitch[0].upper()]

    # Add any number of accidentals
    for acc in pitch[1:]:
        val += ACCIDENTAL_DVALUES[acc]

    # Relative to root
    if root != "C":
        val -= pitch_class_value(root)

    # Mod? (keep in 0--11)
    if mod:
        val %= 12

    if not 0 <= val < 12:  # e.g., Cb, B##
        warnings.warn("computed pitch class value outside 0--11")

    return val


def _validate_pitch_class_name(name: str) -> None:
    """1 or 2 #/b, 1 =, or no accidentals."""
    acc = name[1:]
    if acc:
        msg0 = f"invalid pitch class name {name!r}"
        if any(c not in ACCIDENTAL_DVALUES for c in acc):
            raise ValueError(
                f"{msg0}. Invalid accidental symbol. "
                f"Valid ones are: {', '.join(ACCIDENTAL_DVALUES)}"
            )

        acc_set = set(acc)
        n_acc = len(acc)

        if len(acc_set) != 1:
            raise ValueError(f"{msg0}. Mixed #/b/= not allowed.")

        if acc_set in ({"#"}, {"b"}) and n_acc > 2:
            raise ValueError(f"{msg0}. 2 #/b at most allowed.")
        elif acc_set == {"="} and n_acc > 1:
            raise ValueError(f"{msg0}. 1 = at most allowed.")


class PitchClass:
    """Pitch without octave.
    Value as integer chromatic distance from C.
    """

    def __init__(self, value: int):
        """
        Parameters
        ----------
        value
            Chromatic note value relative to C.
        """
        self.value: int = value % 12
        """Pitch class value, as integer chromatic distance from the root (0--11)."""

        self._name: Optional[str] = None

    @property
    def name(self) -> str:
        """The note (pitch class) name (ASCII)."""
        if self._name is None:
            return NICE_C_CHROMATIC_NOTES[self.value % 12]
        else:
            return self._name

    @property
    def nat(self) -> str:
        """Natural note name (without accidentals)."""
        return self.name[0]

    @property
    def acc(self) -> str:
        """Accidentals in the note name."""
        return self.name[1:]

    # TODO: .isnat(ural)?

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(value={self.value})"

    def _repr_html_(self):
        name = self.name
        return name[0] + "".join(_ACCIDENTAL_ASCII_TO_HTML[c] for c in name[1:])

    @classmethod
    def from_pitch(cls, p: "Pitch") -> "PitchClass":
        return cls.from_name(p.name)

    @classmethod
    def from_name(cls, name: str) -> "PitchClass":
        _validate_pitch_class_name(name)

        value = pitch_class_value(name, mod=True)

        pc = cls(value)
        pc._name = name

        return pc

    @property
    def equivalent_sharp(self) -> "PitchClass":
        pcnew = self - 1
        if len(pcnew.name) == 1:
            return PitchClass.from_name(pcnew.name + "#")
        else:
            pcnew = self - 2
            return PitchClass.from_name(pcnew.name + "##")

    @property
    def equivalent_flat(self) -> "PitchClass":
        pcnew = self + 1
        if len(pcnew.name) == 1:
            return PitchClass.from_name(pcnew.name + "b")
        else:
            pcnew = self + 2
            return PitchClass.from_name(pcnew.name + "bb")

    @property
    def equivalent_natural(self) -> Optional["PitchClass"]:
        pcnew = type(self)(self.value)
        if not pcnew.acc:
            return pcnew
        else:
            return None

    def to_pitch(self, octave: int) -> "Pitch":
        return Pitch.from_class_value(self.value, octave)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.value == other.value

    def __add__(self, x):
        if isinstance(x, int):
            return type(self)(self.value + x)
        elif isinstance(x, type(self)):
            vnew = self.value + x.value
            return type(self)(vnew)
        elif isinstance(x, SimpleInterval):
            # elif type(x) is SimpleInterval:
            return type(self)(self.value + x.value)
        else:
            return NotImplemented

    def __mul__(self, x):
        if not isinstance(x, int):
            return NotImplemented

        return type(self)(x * self.value)

    def __rmul__(self, x):
        return self * x

    def __neg__(self):
        return -1 * self

    def __sub__(self, x):
        if isinstance(x, int):
            return self + -x
        elif isinstance(x, type(self)):
            return SimpleInterval(self.value - x.value)
        else:
            return NotImplemented


# TODO: .from_name as alias for .from_spn / .from_scientific_pitch_notation
@functools.total_ordering
class Pitch:
    """A pitch with value relative to C0.
    Note names are expressed in the context of C major.
    """

    # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L204-L293
    def __init__(self, value: int):
        """
        Parameters
        ----------
        value
            Chromatic note value relative to C0.
        """

        self.value = value
        """Chromatic note value relative to C0."""

        self._class_name: Optional[str] = None

    @property
    def class_value(self) -> int:
        """Chromatic note value of the corresponding pitch class, relative to C."""
        return self.value % 12

    @property
    def octave(self) -> int:
        """Octave number (e.g., A4/A440 is in octave 4)."""
        return self.value // 12

    @property
    def class_name(self) -> str:
        """Note name (pitch class)."""
        if self._class_name is None:
            return NICE_C_CHROMATIC_NOTES[self.class_value]
        else:
            return self._class_name

    @property
    def name(self) -> str:
        """Note name with octave, e.g., C4, Bb2.
        (ASCII scientific pitch notation.)
        """
        return f"{self.class_name}{self.octave}"

    def __str__(self):
        return self.name

    def __repr__(self):
        # return f"{self.__class__.__name__}(name='{self.name}', value={self.value}, octave={self.octave})"
        return f"{self.__class__.__name__}(value={self.value})"

    def _repr_html_(self):
        cn = self.to_pitch_class()._repr_html_()
        return f"{cn}<sub>{self.octave}</sub>"

    @property
    def piano_key_number(self) -> int:
        """For example, middle C (C4) is 40."""
        return self.value - 8

    @property
    def n(self) -> int:
        """Alias for piano_key_number."""
        return self.piano_key_number

    @property
    def equal_temperament_frequency(self) -> float:
        """Piano key frequency.

        https://en.wikipedia.org/wiki/Piano_key_frequencies
        """
        if self.octave is None:
            raise Exception("cannot determine frequency without a specified octave")

        n = self.n

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

        return cls.from_class_value(value=v, octave=o)

    @classmethod
    def from_name(cls, name: str) -> "Pitch":
        """From scientific pitch notation (SPN).

        https://en.wikipedia.org/wiki/Scientific_pitch_notation
        """
        name = name.strip()

        m = _RE_PITCH.fullmatch(name)
        if m is None:
            raise ValueError(f"invalid pitch name '{name}'")

        d = m.groupdict()
        class_name = d["pitch_class"]
        octave = int(d["octave"])

        _validate_pitch_class_name(class_name)

        class_value = pitch_class_value(class_name)

        p = cls.from_class_value(class_value, octave)
        p._class_name = class_name

        return p

    @classmethod
    def from_class_value(cls, value: int, octave: int) -> "Pitch":
        return cls(value + octave * 12)

    @classmethod
    def from_class_name(cls, class_name: str, octave: int) -> "Pitch":
        return cls.from_name(f"{class_name}{octave}")

    @classmethod
    def from_pitch_class(cls, pc: PitchClass, octave: int) -> "Pitch":
        return cls(pc.value + octave)

    def to_pitch_class(self) -> PitchClass:
        return PitchClass.from_name(self.class_name)

    def to_note(self, *, duration: Optional[Fraction] = None):
        from .note import _DEFAULT_UNIT_DURATION, Note

        if duration is None:
            duration = _DEFAULT_UNIT_DURATION

        return Note(self.value, duration=duration)

    def __eq__(self, other):
        # Only for other Pitch instances
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.value == other.value

    def __lt__(self, other):
        # Only for other Pitch instances
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.value < other.value

    def __add__(self, x):
        if isinstance(x, int):
            return type(self)(self.value + x)
        elif isinstance(x, (type(self), SimpleInterval)):
            # NOTE: Adding chromatic-value-wise, not frequency-wise!
            return type(self)(self.value + x.value)
        else:
            return NotImplemented

    def __mul__(self, x):
        if not isinstance(x, int):
            return NotImplemented

        return type(self)(x * self.value)

    def __rmul__(self, x):
        return self * x

    def __neg__(self):
        return -1 * self

    def __sub__(self, x):
        if isinstance(x, int):
            return self + -x
        elif isinstance(x, SimpleInterval):
            return self + -x.value
        elif isinstance(x, type(self)):
            return SignedInterval(self.value - x.value)
        else:
            return NotImplemented


# TODO: make the note types hashable


# https://en.wikipedia.org/wiki/File:Main_intervals_from_C.png
MAIN_INTERVAL_SHORT_NAMES = [
    "P1",
    "m2",
    "M2",
    "m3",
    "M3",
    "P4",
    "A4",
    "P5",
    "m6",
    "M6",
    "m7",
    "M7",
    "P8",
]


@functools.total_ordering
class SimpleInterval:
    """An interval that is at most one octave.
    Direction, e.g., in a melodic interval, is not incorporated.
    """

    def __init__(self, value: int) -> None:

        if 0 <= value <= 12:
            value_ = value
        else:
            abs_value = abs(value)
            mod_abs_value = abs_value % 12
            if mod_abs_value == 0 and abs_value >= 12:
                value_ = 12
            else:
                value_ = mod_abs_value
            warnings.warn(
                f"input value {value} not between 0 and 12 " f"has been coerced to {value_}"
            )
        self.value = value_
        """Number of semitones (half-steps)."""

    @property
    def name(self) -> str:
        """Major, minor, or perfect interval short name."""
        return MAIN_INTERVAL_SHORT_NAMES[self.value]

    @property
    def whole_steps(self) -> float:
        return self.value / 2

    @property
    def inverse(self) -> "SimpleInterval":
        return type(self)(12 - self.value)

    @classmethod
    def from_name(cls, name: str) -> "SimpleInterval":
        if name not in MAIN_INTERVAL_SHORT_NAMES:
            raise ValueError(f"interval name {name!r} not recognized")

        return cls(MAIN_INTERVAL_SHORT_NAMES.index(name))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{type(self).__name__}(value={self.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.value < other.value


class SignedInterval(SimpleInterval):
    """An interval that can be more than one octave and with sign (direction) included."""

    def __init__(self, value: int) -> None:

        self.value = value
        """Number of semitones (half-steps)."""

    @property
    def name(self) -> str:
        is_neg = self.value < 0

        n_o, i0 = divmod(abs(self.value), 12)

        if n_o >= 2:
            s_o = f"{n_o}({MAIN_INTERVAL_SHORT_NAMES[-1]})"
        elif n_o == 1:
            s_o = f"{MAIN_INTERVAL_SHORT_NAMES[-1]}"
        else:  # 0
            s_o = ""

        s_i0 = MAIN_INTERVAL_SHORT_NAMES[i0] if i0 != 0 else ""

        if s_o and not s_i0:
            s = s_o
        elif s_i0 and not s_o:
            s = s_i0
        elif not s_o and not s_i0:
            s = MAIN_INTERVAL_SHORT_NAMES[0]
        else:
            s = f"{s_o}+{s_i0}"

        if is_neg:
            s = f"-[{s}]"

        return s
