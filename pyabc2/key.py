"""
Key (e.g., G, Em, Ador)
"""
# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
import re
import warnings
from typing import Dict, List, Optional, Tuple

from .pitch import PitchClass

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


CHROMATIC_VALUES_IN_MAJOR = [0, 2, 4, 5, 7, 9, 11]

MODE_SCALE_DEGREE = {
    "major": 1,
    "ionian": 1,
    "dorian": 2,
    "phrygian": 3,
    "lydian": 4,
    "mixolydian": 5,
    "minor": 6,
    "aeolian": 6,
    "locrian": 7,
}
"""Scale degree of the major scale that we would set as the tonic to get the given mode.
For example, if we start on A within the context of the C major scale (scale degree 6),
we get A minor.
"""


def _scale_chromatic_values(mode: str) -> List[int]:
    i = MODE_SCALE_DEGREE[mode]
    i0 = i - 1

    vs_wrt_major = CHROMATIC_VALUES_IN_MAJOR[i0:] + CHROMATIC_VALUES_IN_MAJOR[:i0]
    dv = MODE_VALUES[mode]

    return [(v + dv) % 12 for v in vs_wrt_major]


def _scale_intervals(
    values: List[int],
    *,
    include_upper: bool = True,
) -> List[str]:
    """Return list of intervals ('W' or 'H').

    Parameters
    ----------
    values
        Chromatic values (7 of them).
    include_upper : bool, optional
        Whether to return 7 intervals by computing the interval from scale degree 7 to 8,
        by default True.
    """
    assert len(values) == 7

    if include_upper:
        values.append(12)

    intervals = []
    for v1, v2 in zip(values[:-1], values[1:]):
        dv = v2 - v1
        if dv == 2:
            interval = "W"
        elif dv == 1:
            interval = "H"
        else:
            raise ValueError("strange interval (not W/H)")
        intervals.append(interval)
    # TODO: should make a class for interval!

    return intervals


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

SHARP_ORDER = list("FCGDAEB")
FLAT_ORDER = list("BEADGCF")


class Key:
    """Key, including mode."""

    # TODO: maybe should move name to a .from_name for consistency with Pitch(Class)
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
            self.root = PitchClass.from_name(root)
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
        if extra != "":
            warnings.warn(f"extra info {extra!r} in key spec {key!r} ignored")

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

        return PitchClass.from_name(base + acc), mode
        # TODO: probably should either return a Key or be private / maybe outside class

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
        root = PitchClass((key.value + rel) % 12)

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
        root = PitchClass((key.value + rel) % 12)

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

    @property
    def scale(self) -> List[PitchClass]:
        """Notes (pitch classes) of the scale."""
        pc1 = self.root
        return [pc1 + v for v in _scale_chromatic_values(self.mode)]

    def print_scale(self) -> None:
        print(" ".join(str(pc) for pc in self.scale))

    # TODO: scale as scale degrees in the major context
    # TODO: scale cf. major/minor?

    def __str__(self):
        return f"{self.root.name}{self.mode[:3]}"

    def __repr__(self):
        return f"Key(root={self.root.name}, mode={self.mode})"

    def __eq__(self, other):
        if isinstance(other, Key):
            return self.root == other.root and _mode_is_equiv(self.mode, other.mode)
        else:
            return NotImplemented
