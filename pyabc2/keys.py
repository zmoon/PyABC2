"""
Pitches, notes, keys and their relations
"""
# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
import re
import warnings
from typing import Dict, List, Optional, Tuple, Union


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
        self.value = Pitch.pitch_value(name, root=root)
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
        return CHROMATIC_SCALE_DEGREE[self.value]

    def with_root(self, root: str) -> "PitchClass":
        """New root."""
        v = self.value
        vr = PITCH_VALUES_WRT_C[self.root]
        vrnew = PITCH_VALUES_WRT_C[root]
        return PitchClass.from_value((v + vr - vrnew) % 12, root=root)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError

        return self.value == other.with_root(self.root).value


class Pitch:  # TODO: maybe separate relative pitch / pitch class (no octave) to simplify this one
    """A note value relative to C, possibly with octave specified."""

    # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L204-L293
    def __init__(self, value: Union[int, str, "Pitch"], octave: Optional[int] = None):
        """
        Parameters
        ----------
        value
            Relative note value OR note name OR existing Pitch instance.
        octave
            Octave. By default octave is treated as unspecified.
        """
        self._name: Optional[str]
        self._value: int
        self._octave: Optional[int]

        # if isinstance(value, Note):
        #     self._note = value

        #     if len(value.note) == 1:
        #         acc = value.key.accidentals.get(value.note[0].upper(), '')
        #         self._name = value.note.upper() + acc
        #         self._value = self.pitch_value(self._name)
        #     else:
        #         self._name = value.note.capitalize()
        #         self._value = self.pitch_value(value.note)

        #     assert octave is None
        #     self._octave = value.octave

        if isinstance(value, str):
            self._name = value
            self._value = self.pitch_value(value)
            self._octave = octave

        elif isinstance(value, Pitch):
            self._name = value._name
            self._value = value._value
            self._octave = value._octave

        elif isinstance(value, int):
            self._name = None
            if octave is None:
                self._value = value
                self._octave = octave
            else:
                self._value = value % 12
                self._octave = octave + (value // 12)

        else:
            raise TypeError("invalid `value`")

    def __repr__(self):
        return f"Pitch(name='{self.name}', value={self.value}, octave={self.octave})"

    @property
    def name(self) -> str:
        """Note name (pitch class)."""
        if self._name is not None:
            return self._name
        return CHROMATIC_NOTES[self.value % 12]

    @property
    def value(self) -> int:
        """Relative note value."""
        return self._value

    @property
    def octave(self) -> Optional[int]:
        """Octave."""
        return self._octave

    @property
    def abs_value(self):
        if self.octave is None:
            raise Exception("absolute value not meaningful with unspecified octave")

        return self.value + self.octave * 12

    @staticmethod
    def pitch_value(pitch: str, root: str = "C") -> int:
        """Convert a pitch string like "A#" to a chromatic scale value relative
        to root.
        """
        pitch = pitch.strip()
        val = PITCH_VALUES_WRT_C[pitch[0].upper()]
        for acc in pitch[1:]:
            val += ACCIDENTAL_DVALUES[acc]
        if root != "C":
            val = (val - Pitch.pitch_value(root)) % 12
        if not 0 <= val < 12:  # e.g., Cb, B##
            warnings.warn("computed pitch value outside 0--11")
        return val

    @property
    def equivalent_sharp(self) -> "Pitch":
        p = self - 1
        if len(p.name) == 1:
            return Pitch(p.name + "#", octave=self.octave)
        else:
            return Pitch((self - 2).name + "##", octave=self.octave)

    @property
    def equivalent_flat(self) -> "Pitch":
        p = self + 1
        if len(p.name) == 1:
            return Pitch(p.name + "b", octave=self.octave)
        else:
            return Pitch((self + 2).name + "bb", octave=self.octave)

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

    # @classmethod
    # def from_name(cls, name: str) -> "Pitch":
    #     m = _re_pitch.match(name)
    #     if m is None:
    #         raise ValueError(f"invalid pitch name '{name}'")

    #     d = m.groupdict()
    #     base_name = d["name"]
    #     acc = d["acc"]
    #     octave = d["oct"]
    #     return cls()

    def __eq__(self, other):
        # Only for other Pitch instances
        if (self.octave is None) and (other.octave is None):
            return self.value == other.value
        elif (self.octave is None) ^ (other.octave is None):  # xor
            raise Exception("comparison ambiguous since one doesn't have octave set")
        else:
            return self.value == other.value and self.octave == other.octave

    def __add__(self, x):
        if isinstance(x, int):
            return Pitch(self.value + x, octave=self.octave)
        else:
            raise NotImplementedError

    def __sub__(self, x):
        return self + -x


if __name__ == "__main__":

    assert Pitch.pitch_value("C###") == Pitch.pitch_value("Eb")


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
            self.root = Pitch(root)
            self.mode = mode

    @staticmethod
    def parse_key(key: str) -> Tuple["Pitch", str]:
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

        return Pitch(base + acc), mode

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
        root = Pitch((key.value + rel) % 12)

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
        root = Pitch((key.value + rel) % 12)

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
