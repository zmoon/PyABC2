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

ACCIDENTAL_DVALUES = {"": 0, "#": 1, "b": -1}
"""Change in value associated with a certain accidental mark (`#` or `b`)."""

ACCIDENTAL_ASCII_TO_UNICODE = {"": "", "#": "♯", "b": "♭", "##": "𝄪", "bb": "𝄫", "=": "♮"}
ACCIDENTAL_ASCII_TO_PM = {"": "", "#": "+", "b": "-", "=": "="}

CHROMATIC_NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
"""ASCII chromatic notes, starting with C at index 0."""

# https://en.wikipedia.org/wiki/Solf%C3%A8ge#Movable_do_solf%C3%A8ge
CHROMATIC_SOLFEGE = ["Do", "Di", "Re", "Me", "Mi", "Fa", "Fi", "Sol", "Le", "La", "Te", "Ti"]

CHROMATIC_SCALE_DEGREE = ["1", "#1", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7"]


_S_RE_PITCH_CLASS = r"[A-G][\#b]*"
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


def _to_roman(n: int) -> str:
    # based on https://stackoverflow.com/a/47713392
    if n >= 40:  # XL
        raise NotImplementedError
    roman_vals = (
        # ...
        (10, "X"),
        (9, "XI"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    chars = []
    for i, r in roman_vals:
        f, n = divmod(n, i)
        chars.append(r * f)
        if n == 0:
            break
    return "".join(chars)


# TODO: maybe a simplier PitchClass without root that PitchClass and Pitch could both inherit from


class PitchClass:
    """Pitch without octave."""

    # TODO: rooting can be done easily by just subtracting from an instance, so `root` not needed?

    def __init__(self, value: int, *, root: str = "C"):
        """
        Parameters
        ----------
        value
            Chromatic note value relative to the root.
        root
            The note set to have value=0 (normally C, which is the default).
            The root determines what value this pitch class has.
        """
        self.value = value
        """Pitch class value, as integer chromatic distance from the root (0--11)."""

        self.root = root
        """The name of the root note (pitch class)."""

    @property
    def name(self) -> str:
        """The note (pitch class) name (ASCII)."""
        vr = PITCH_VALUES_WRT_C[self.root]
        v0 = self.value + vr
        return CHROMATIC_NOTES[v0 % 12]  # TODO: correct note/acc based on root?

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(value={self.value}, root='{self.root}')"

    @classmethod
    def from_pitch(cls, p: "Pitch") -> "PitchClass":
        return cls.from_name(p.name)

    @classmethod
    def from_name(cls, name: str, *, root: str = "C") -> "PitchClass":
        value = pitch_class_value(name, root=root, mod=True)

        return cls(value, root=root)

    # TODO: scale degree and such for any mode?

    @property
    def solfege(self) -> str:
        """Solfege symbol. Accidentals allowed."""
        return CHROMATIC_SOLFEGE[self.value]

    @property
    def scale_degree(self) -> int:
        """Scale degree within the root's Ionian scale."""
        from .key import CHROMATIC_VALUES_IN_MAJOR

        if self.value not in CHROMATIC_VALUES_IN_MAJOR:
            raise Exception(f"{self} is not in {self.root}'s major scale")

        return int(CHROMATIC_SCALE_DEGREE[self.value])

    def scale_degree_chromatic(
        self, *, number_format: str = "arabic", acc_format: str = "ascii"
    ) -> str:
        """String representation of scale degree, allowing for raised/lowered wrt. major scale.

        Parameters
        ----------
        number_format : {"arabic", "roman", "roman_lower"}
        acc_format : {"ascii", "unicode", "pm"}
        """
        s = CHROMATIC_SCALE_DEGREE[self.value]  # ascii arabic
        if len(s) == 2:
            acc, n = s[0], int(s[1])
        else:
            acc, n = "", int(s)

        # Adjust accidental repr
        if acc_format == "unicode":
            acc = ACCIDENTAL_ASCII_TO_UNICODE[acc]
        elif acc_format == "ascii":
            pass
        elif acc_format == "pm":
            acc = ACCIDENTAL_ASCII_TO_PM[acc]
        else:
            raise ValueError("invalid `acc_format`")

        # Number repr
        if number_format == "arabic":
            s_n = str(n)
        elif number_format == "roman":
            s_n = str(_to_roman(n))
        elif number_format == "roman_lower":
            s_n = str(_to_roman(n)).lower()
        else:
            raise ValueError("invalid `number_format`")

        if acc_format == "pm":
            return s_n + acc
        else:
            return acc + s_n

    @property
    def equivalent_sharp(self) -> "PitchClass":
        pnew = self - 1
        # TODO: currently these names just get reset with the new name property
        if len(pnew.name) == 1:
            return PitchClass.from_name(pnew.name + "#", root=self.root)
        else:
            pnew = self - 2
            return PitchClass.from_name(pnew.name + "##", root=self.root)

    @property
    def equivalent_flat(self) -> "PitchClass":
        pnew = self + 1
        if len(pnew.name) == 1:
            return PitchClass.from_name(pnew.name + "b", root=self.root)
        else:
            pnew = self + 2
            return PitchClass.from_name(pnew.name + "bb", root=self.root)

    def with_root(self, root: str) -> "PitchClass":
        """New instance with a (possibly) different root."""
        v = self.value
        vr = PITCH_VALUES_WRT_C[self.root]
        vrnew = PITCH_VALUES_WRT_C[root]
        return PitchClass((v + vr - vrnew) % 12, root=root)

    def to_pitch(self, octave: int) -> "Pitch":
        return Pitch.from_class_value(self.with_root("C").value, octave)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.value == other.with_root(self.root).value

    def __add__(self, x):
        if isinstance(x, int):
            return PitchClass(self.value + x, root=self.root)
        elif isinstance(x, PitchClass):
            vnew = self.value + x.with_root(self.root).value
            return PitchClass(vnew, root=self.root)
        elif isinstance(x, SimpleInterval):
            # elif type(x) is SimpleInterval:
            return PitchClass(self.value + x.value, root=self.root)
        else:
            return NotImplemented

    def __mul__(self, x):
        if not isinstance(x, int):
            return NotImplemented

        return PitchClass(x * self.value, root=self.root)

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
    """A pitch with value relative to C0."""

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
        return CHROMATIC_NOTES[self.class_value]

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

        class_value = pitch_class_value(class_name)

        return cls.from_class_value(class_value, octave)

    @classmethod
    def from_class_value(cls, value: int, octave: int) -> "Pitch":
        return cls(value + octave * 12)

    # TODO: from_class_name

    @classmethod
    def from_pitch_class(cls, pc: PitchClass, octave: int) -> "Pitch":
        return cls(pc.with_root("C").value + octave)

    def to_pitch_class(self, *, root: str = "C") -> PitchClass:
        return PitchClass.from_name(self.class_name, root=root)

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
            # Adding chromatic-value-wise, not frequency-wise!
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
