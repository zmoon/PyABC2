"""
Pitch class (e.g., C), Pitch (e.g., C4)
"""

# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
import functools
import re
import warnings
from fractions import Fraction
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .key import Key


def _gen_pitch_values() -> dict[str, int]:
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
_TRAN_NUM_TO_UNICODE = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

NICE_C_CHROMATIC_NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]
"""ASCII chromatic notes, starting with C at index 0.
The more common accidentals are used.
"""

_S_RE_ASCII_ACCIDENTALS = r"(?:##|bb|b|#|=)"
_S_RE_PITCH_CLASS = rf"[A-G]{_S_RE_ASCII_ACCIDENTALS}?"
_S_RE_LOWER_PITCH_CLASS = rf"[a-g]{_S_RE_ASCII_ACCIDENTALS}?"
_RE_PITCH_CLASS = re.compile(_S_RE_PITCH_CLASS)
# _S_RE_PITCH_CLASS_ONE_ACC = r"[A-G][\#|b]?"
_RE_PITCH = re.compile(rf"(?P<pitch_class>{_S_RE_PITCH_CLASS})" r"\s*" r"(?P<octave>[0-9]+)")


def pitch_class_value(pitch: str, root: str = "C", *, mod: bool = False) -> int:
    """Convert a pitch string like 'A#' (note name / pitch class)
    to a chromatic scale value in 0--11 relative to root.
    """
    pitch = pitch.strip()

    if not _RE_PITCH_CLASS.fullmatch(pitch):
        raise ValueError(
            f"invalid pitch class specification '{pitch}'; Should match '{_RE_PITCH_CLASS.pattern}'"
        )

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


def _to_roman(n: int) -> str:
    # based on https://stackoverflow.com/a/47713392
    if n >= 40:  # XL
        raise NotImplementedError
    roman_vals = (
        # ...
        (10, "X"),
        (9, "IX"),
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


class PitchClass:
    """Pitch without octave.
    Value as integer chromatic distance from C in semitones (half steps).

    Parameters
    ----------
    value
        Chromatic distance from C in semitones (half steps).
        For example, C is 0, D is 2, B is 11.

    Examples
    --------
    >>> from pyabc2 import PitchClass
    >>> PitchClass(0)
    PitchClass(value=0, name='C')
    >>> PitchClass(2)
    PitchClass(value=2, name='D')
    >>> PitchClass(11)
    PitchClass(value=11, name='B')

    >>> PitchClass.from_name('Bb')
    PitchClass(value=10, name='Bb')

    >>> PitchClass.from_name('E#')
    PitchClass(value=5, name='E#')
    >>> PitchClass(5)
    PitchClass(value=5, name='F')
    """

    def __init__(self, value: int):
        self.value: int = value % 12
        """Pitch class value
        (integer chromatic distance from C in semitones (half steps)).
        """

        self._name: str | None = None

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

    @property
    def dvalue_acc(self) -> int:
        """Relative chromatic value of the accidentals."""
        return self.acc.count("#") - self.acc.count("b")

    @property
    def value_nat(self) -> int:
        """Chromatic value ignoring accidentals."""
        return self.value - self.dvalue_acc

    @property
    def isnat(self) -> bool:
        return self.acc in {"", "="}

    @property
    def isflat(self) -> bool:
        return "b" in self.acc

    @property
    def issharp(self) -> bool:
        return "#" in self.acc

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{type(self).__name__}(value={self.value}, name={self.name!r})"

    def _repr_html_(self):
        return f"{self.nat}{_ACCIDENTAL_ASCII_TO_HTML[self.acc]}"

    def unicode(self):
        """String repr using unicode accidental symbols.

        .. note::
           ``str(pitch_class)`` returns an string representation using ASCII accidental symbols
           (``#``, ``b``, ``=``).
        """
        return f"{self.nat}{_ACCIDENTAL_ASCII_TO_UNICODE[self.acc]}"

    @classmethod
    def from_pitch(cls, p: "Pitch") -> "PitchClass":
        """From pitch instance."""
        return cls.from_name(p.class_name)

    @classmethod
    def from_name(cls, name: str) -> "PitchClass":
        """From pitch class name (e.g., ``C``, ``F#``).

        `name` is preserved (:attr:`name`) if using this initializer.
        """
        _validate_pitch_class_name(name)

        value = pitch_class_value(name, mod=True)

        pc = cls(value)
        pc._name = name

        return pc

    # TODO: PitchClass from value with acc option (to hint name)?

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
        if pcnew.isnat:
            return pcnew
        else:
            return None

    def value_in(self, key: "Key", *, mod: bool = True) -> int:
        """Chromatic value in key.
        Use `mod=False` to obtain negatives.
        """
        v0 = PITCH_VALUES_WRT_C[key.tonic.name]
        if mod:
            return (self.value - v0) % 12
        else:
            import warnings

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")

                return pitch_class_value(self.name) - v0

    def scale_degree_int_in(self, key: "Key") -> int:
        """Integer scale degree in key.
        Raises ValueError if the note is not in the scale.
        """
        v = self.value_in(key, mod=True)

        scvs = key.scale_chromatic_values

        inat = key._letters.index(self.nat) + 1

        try:
            i = scvs.index(v) + 1

        except ValueError as e:
            raise ValueError(f"{self.name} is not in the {key.tonic} {key.mode} scale.") from e

        if inat != i:
            raise ValueError(f"{self.name} is not in the {key.tonic} {key.mode} scale.")

        return i

    def scale_degree_in(
        self, key: "Key", *, num_fmt: str = "arabic", acc_fmt: str = "ascii"
    ) -> str:
        """String representation of scale degree allowing #/b."""

        # If name has not been explicitly set, we can't differentiate between #/b.
        use_enh = self._name is None
        # TODO: .isenh property?

        i = key._letters.index(self.nat) + 1

        dv = self.dvalue_acc - key.scale[i - 1].dvalue_acc

        assert 0 <= abs(dv) <= 2

        # 0. First form the arabic/ascii version
        if use_enh:
            # NOTE: Max of one acc if `use_enh`
            assert 0 <= abs(dv) <= 1
            if dv == 1:
                s = f"#{i}/b{i+1}"
            elif dv == -1:
                s = f"#{i-1}/b{i}"
            else:
                s = f"{i}"
        else:
            if dv < 0:
                acc = "b" * abs(dv)
            elif dv > 0:
                acc = "#" * dv
            else:
                # acc = self.acc  # "" or "="
                acc = ""
            s = f"{acc}{i}"

        # 1. Adjust numbers if desired
        num_fmt_ = num_fmt.lower()
        if num_fmt_ == "arabic":
            pass
        elif num_fmt_ == "roman":
            s = re.sub(r"[0-9]", lambda m: _to_roman(int(m.group(0))), s)
        else:
            raise ValueError("invalid `num_fmt`")

        # 2. Adjust accidentals if desired
        acc_fmt_ = acc_fmt.lower()
        if acc_fmt_ == "ascii":
            pass
        elif acc_fmt_ == "unicode":
            s = re.sub(
                _S_RE_ASCII_ACCIDENTALS, lambda m: _ACCIDENTAL_ASCII_TO_UNICODE[m.group(0)], s
            )
        else:
            raise ValueError("invalid `acc_fmt`")

        # TODO: could make a helper fn for the above things to use elsewhere

        return s

    def solfege_in(self, key: "Key") -> str:
        """Solfège symbol in the context of a given key.

        https://en.wikipedia.org/wiki/Solf%C3%A8ge#Movable_do_solf%C3%A8ge
        """
        from .key import CHROMATIC_SOLFEGE_ALL

        if key._mode not in {"maj", "ion"}:
            raise NotImplementedError("solfège only implemented for major")

        if len(self.acc) == 2:
            raise ValueError("solfège not defined for ##/bb notes")

        use_enh = self._name is None  # see `.scale_degree_in`

        v = self.value_in(key, mod=True)
        if use_enh:
            solfs = CHROMATIC_SOLFEGE_ALL[v]
            s = "/".join(solfs)

        else:
            inat0 = key._letters.index(self.nat)
            scvs = key.scale_chromatic_values
            vnat = scvs[inat0]

            dv = self.dvalue_acc - key.scale[inat0].dvalue_acc

            absdv = abs(dv)
            if absdv > 1:
                raise ValueError(f"solfège not defined for {self.scale_degree_in(key)}")
            elif absdv == 1:
                try:
                    if dv < 0:
                        s = CHROMATIC_SOLFEGE_ALL[vnat - 1][1]
                    elif dv > 0:
                        s = CHROMATIC_SOLFEGE_ALL[vnat + 1][0]
                except IndexError:
                    raise ValueError(f"solfège not defined for {self.scale_degree_in(key)}")
            else:
                t = CHROMATIC_SOLFEGE_ALL[v]
                assert len(t) == 1
                s = t[0]

        return s

    def to_pitch(self, octave: int) -> "Pitch":
        """Convert to pitch in the specified octave."""
        p = Pitch.from_class_value(self.value, octave)
        p._class_name = self._name

        return p

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

    Parameters
    ----------
    value
        Chromatic distance from C0 in semitones (half steps).
        For example, C4 (middle C) is 48, A4 is 57.

    Examples
    --------
    >>> from pyabc2 import Pitch
    >>> Pitch(48)
    Pitch(value=48, name='C4')
    >>> Pitch(57)
    Pitch(value=57, name='A4')

    >>> Pitch.from_name('E#3')
    Pitch(value=41, name='E#3')
    >>> Pitch(41)
    Pitch(value=41, name='F3')

    >>> Pitch.from_etf(440)  # Hz
    Pitch(value=57, name='A4')
    """

    # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L204-L293
    def __init__(self, value: int):

        self.value: int = value
        """Pitch value
        (integer chromatic distance from C0 in semitones (half steps)).
        """

        self._class_name: str | None = None
        self._octave: int | None = None
        # TODO: we should be able to determine octave from value and class name
        # in the case that _class_name is set

    @property
    def class_value(self) -> int:
        """Chromatic note value of the corresponding pitch class, relative to C."""
        return self.value % 12

    @property
    def octave(self) -> int:
        """Octave number (e.g., A4/A440 is in octave 4)."""
        if self._octave is None:
            return self.value // 12
        else:
            return self._octave

    @property
    def class_name(self) -> str:
        """Note name (pitch class)."""
        if self._class_name is None:
            return NICE_C_CHROMATIC_NOTES[self.class_value]
        else:
            return self._class_name

    @property
    def name(self) -> str:
        """Note (pitch) name with octave, e.g., C4, Bb2.
        (ASCII scientific pitch notation.)
        """
        return f"{self.class_name}{self.octave}"

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{type(self).__name__}(value={self.value}, name={self.name!r})"

    def _repr_html_(self):
        cn = self.to_pitch_class()._repr_html_()
        return f"{cn}<sub>{self.octave}</sub>"

    @property
    def helmholtz(self) -> str:
        """Pitch name in Helmholtz pitch notation, e.g. ``C,`` and ``c'`` (ASCII)."""
        little_c_octave = self.octave - 3
        if little_c_octave >= 0:
            return self.class_name.lower() + "'" * little_c_octave
        big_c_octave = -self.octave + 2
        return self.class_name + "," * big_c_octave

    @classmethod
    def from_helmholtz(cls, helmholtz_name: str) -> "Pitch":
        """From Helmholtz pitch notation.

        https://en.wikipedia.org/wiki/Helmholtz_pitch_notation
        """
        helmholtz_name = helmholtz_name.strip()
        # Single character range so it doesn't fail on empty string.
        is_upper = helmholtz_name[0:1].isupper()
        helmoltz_re = (
            rf"({_S_RE_PITCH_CLASS})(,*)" if is_upper else rf"({_S_RE_LOWER_PITCH_CLASS})('*)"
        )
        m = re.fullmatch(helmoltz_re, helmholtz_name)
        if m is None:
            raise ValueError(f"invalid Helmholtz pitch name '{helmholtz_name}'")
        pitch_class_name = m.group(1).title()
        marks = len(m.group(2))
        octave = -marks + 2 if is_upper else marks + 3

        return Pitch.from_class_name(pitch_class_name, octave)

    def unicode(self):
        """String repr using unicode accidental symbols and unicode subscripts for octave.

        .. note::
           ``str(pitch)`` returns an string representation using ASCII accidental symbols
           (``#``, ``b``, ``=``).
        """
        cn = self.to_pitch_class().unicode()
        o = str(self.octave).translate(_TRAN_NUM_TO_UNICODE)
        return f"{cn}{o}"

    @property
    def piano_key_number(self) -> int:
        """For example, middle C (C4) is 40."""
        return self.value - 8

    @property
    def n(self) -> int:
        """Alias for :attr:`piano_key_number`."""
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
        """Alias for :attr:`equal_temperament_frequency`."""
        return self.equal_temperament_frequency

    @classmethod
    def from_etf(cls, f: float) -> "Pitch":
        """From frequency, rounding to the nearest piano key."""
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
        # Preserve "non-standard" pitch class name input like Cb,
        # which also affects the value since the octave is set by the natural note name.
        p._class_name = class_name
        p._octave = octave

        return p

    @classmethod
    def from_class_value(cls, value: int, octave: int) -> "Pitch":
        """From pitch class chromatic value and octave."""
        return cls(value + octave * 12)

    @classmethod
    def from_class_name(cls, class_name: str, octave: int) -> "Pitch":
        """From pitch class name and octave."""
        return cls.from_name(f"{class_name}{octave}")

    @classmethod
    def from_pitch_class(cls, pc: PitchClass, octave: int) -> "Pitch":
        """From pitch class instance."""
        p = cls(pc.value + octave * 12)
        p._class_name = pc._name

        return p

    def to_pitch_class(self) -> PitchClass:
        """Convert to pitch class, preserving the class name."""
        # Preserve explicit name if set
        if self._class_name is not None:
            return PitchClass.from_name(self.class_name)
        else:
            return PitchClass(self.class_value)

    def to_note(self, *, duration: Fraction | None = None):
        """Convert to note (eighth note by default)."""
        from .note import _DEFAULT_UNIT_DURATION, Note

        if duration is None:
            duration = _DEFAULT_UNIT_DURATION

        note = Note(self.value, duration=duration)
        note._class_name = self._class_name
        note._octave = self._octave

        return note

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
    "P1",  # aka "U"
    "m2",
    "M2",
    "m3",
    "M3",
    "P4",
    "A4",  # aka "TT"
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
        """Number of semitones (half steps)."""

    @property
    def name(self) -> str:
        """Major, minor, or perfect interval short name."""
        return MAIN_INTERVAL_SHORT_NAMES[self.value]
        # TODO: based on context https://en.wikipedia.org/wiki/Interval_(music)#Main_intervals

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
        """Number of semitones (half steps)."""

    @property
    def name(self) -> str:
        is_neg = self.value < 0

        n_o, i0 = divmod(abs(self.value), 12)

        # TODO: https://en.wikipedia.org/wiki/Interval_(music)#Main_compound_intervals

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
