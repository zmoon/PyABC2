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
            raise TypeError

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
        else:
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
        """
        Return the ionian mode relative to the given key and mode.
        """
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

    def __str__(self):
        return f"{self.root.name}{self.mode[:3]}"

    def __repr__(self):
        return f"Key(root={self.root.name}, mode={self.mode})"

    # def __eq__(self):
