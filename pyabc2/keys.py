"""
Pitches, notes, keys and their relations
"""
# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
import re
import warnings
from typing import Dict, List, Optional, Tuple


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

MODE_VALUES = {
    "major": 0,
    "minor": 3,
    "ionian": 0,
    "aeolian": 3,
    "mixolydian": -7,
    "dorian": -2,
    "phrygian": -4,
    "lydian": -5,
    "locrian": 1,
}
"""Dict. mapping mode names to chromatic step deltas (relative to Ionian)."""

MODE_ABBRS = {m[:3]: m for m in MODE_VALUES}
"""Dict. mapping mode abbreviation to full-length mode name."""


def _mode_is_equiv(m1: str, m2: str) -> bool:
    """Compare modes based on their integer values,
    allowing major == ionian and minor == aeolian.
    """
    return MODE_VALUES[m1] == MODE_VALUES[m2]


IONIAN_SHARPFLAT_COUNT = {
    "C#": 7,
    "F#": 6,
    "B": 5,
    "E": 4,
    "A": 3,
    "D": 2,
    "G": 1,
    "C": 0,
    "F": -1,
    "Bb": -2,
    "Eb": -3,
    "Ab": -4,
    "Db": -5,
    "Gb": -6,
    "Cb": -7,
}
"""Dict. mapping chromatic note to the number of flats/sharps in its Ionian mode."""

SHARP_ORDER = "FCGDAEB"
FLAT_ORDER = "BEADGCF"


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
            raise TypeError

        return self.value == other.with_root(self.root).value

    def __add__(self, x):
        if isinstance(x, int):
            return PitchClass.from_value(self.value + x, root=self.root)
        else:
            raise NotImplementedError

    def __sub__(self, x):
        return self + -x


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
            raise TypeError

        return self.abs_value == other.abs_value

    def __add__(self, x):
        if isinstance(x, int):
            doctave, dvalue = divmod(self.value + x, 12)
            return Pitch(self.value + dvalue, self.octave + doctave)
        else:
            raise NotImplementedError

    def __sub__(self, x):
        return self + -x


class Key:
    """Key, including mode."""

    def __init__(
        self, name: Optional[str] = None, root: Optional[str] = None, mode: Optional[str] = None
    ):
        """
        Parameters
        ---------
        name
            Key name, e.g., `D`, `Ador`, `Bbmin`, ...
        root
            Root of the key, e.g., `C`, `D`, ...
        mode
            Mode specification, e.g., `m`, `min`, `dor`.
            (Major assumed if mode not specified.)
        """
        if name is not None:
            assert root is None and mode is None, "pass either `name` or `root`+`mode`"
            self.root, self.mode = Key.parse_key(name)
        else:
            assert root is not None and mode is not None, "pass either `name` or `root`+`mode`"
            self.root = PitchClass(root)
            self.mode = mode

    @staticmethod
    def parse_key(key: str) -> Tuple[PitchClass, str]:
        # # highland pipe keys
        # if key in ['HP', 'Hp']:
        #     return {'F': 1, 'C': 1, 'G': 0}

        m = re.match(r"([A-G])(\#|b)?\s*(\w+)?(.*)", key)
        if m is None:
            raise ValueError(f"Invalid key specification '{key}'")
        base, acc, mode, extra = m.groups()

        if acc is None:
            acc = ""

        # Default to major
        if mode is None:
            mode = "major"

        # `m` as an alias for `min`
        if mode == "m":
            mode = "minor"

        try:
            mode = MODE_ABBRS[mode[:3].lower()]
        except KeyError:
            raise ValueError("Unrecognized mode specification '{mode}' from key '{key}'")

        return PitchClass(base + acc), mode

    @property
    def key_signature(self) -> List[str]:  # TODO: maybe change name
        """
        List of accidentals that should be displayed in the key
        signature for the given key description.
        """
        # determine number of sharps/flats for this key by first converting
        # to ionian, then doing the key lookup
        key = self.relative_ionian
        num_acc = IONIAN_SHARPFLAT_COUNT[key.root.name]

        sig = []
        # sharps or flats?
        if num_acc > 0:
            for i in range(num_acc):
                sig.append(SHARP_ORDER[i] + "#")
        else:
            for i in range(-num_acc):
                sig.append(FLAT_ORDER[i] + "b")

        return sig

    @property
    def accidentals(self) -> Dict[str, str]:
        """A dictionary of accidentals in the key signature,
        mapping natural note names to the accidental applied.
        """
        return {p: a for p, a in self.key_signature}  # type: ignore[misc, has-type]

    @property
    def relative_ionian(self) -> "Key":
        key, mode = self.root, self.mode
        rel = MODE_VALUES[mode]
        root = PitchClass.from_value((key.value + rel) % 12)

        # Select flat or sharp to match the current key name
        if "#" in key.name:
            root2 = root.equivalent_sharp
            if len(root2.name) == 2:
                root = root2
        elif "b" in key.name:
            root2 = root.equivalent_flat
            if len(root2.name) == 2:
                root = root2

        return Key(root=root.name, mode="ionian")

    @property
    def relative_major(self) -> "Key":
        """Alias for relative_ionian."""
        return self.relative_ionian

    @property
    def relative_aeolian(self) -> "Key":
        # TODO: DRY (possibly make method that can do any relative mode)

        key, mode = self.root, self.mode
        rel = MODE_VALUES[mode] - MODE_VALUES["aeolian"]
        root = PitchClass.from_value((key.value + rel) % 12)

        # Select flat or sharp to match the current key name
        if "#" in key.name:
            root2 = root.equivalent_sharp
            if len(root2.name) == 2:
                root = root2
        elif "b" in key.name:
            root2 = root.equivalent_flat
            if len(root2.name) == 2:
                root = root2

        return Key(root=root.name, mode="aeolian")

    @property
    def relative_minor(self) -> "Key":
        """Alias for relative_aeolian."""
        return self.relative_aeolian

    def __str__(self):
        return f"{self.root.name}{self.mode[:3]}"

    def __repr__(self):
        return f"Key(root={self.root.name}, mode={self.mode})"

    def __eq__(self, other):
        if isinstance(other, Key):
            return self.root == other.root and _mode_is_equiv(self.mode, other.mode)
        else:
            raise TypeError


class Note:
    """A note has a pitch and a duration."""
