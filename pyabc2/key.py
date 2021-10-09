"""
Key (e.g., G, Em, Ador)
"""
# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
import re
import warnings
from typing import Dict, List, Optional, Tuple, Union

from .pitch import PitchClass

MODE_NAMES = [
    "major",
    "minor",
    #
    "ionian",
    "dorian",
    "phrygian",
    "lydian",
    "mixolydian",
    "aeolian",
    "locrian",
]

MODE_ABBR_TO_FULL = {m[:3]: m for m in MODE_NAMES}
"""Dict. mapping mode abbreviation to full-length mode name."""


def _validate_and_normalize_mode_name(mode: str) -> str:
    """Return mode abbreviation if mode recognized."""
    mode_ = mode.lower()
    if mode_ not in MODE_NAMES + list(MODE_ABBR_TO_FULL):
        raise ValueError(f"invalid mode name {mode!r}")

    return mode_[:3]


MODE_VALUES = {
    "maj": 0,
    "min": 3,
    #
    "ion": 0,
    "dor": -2,
    "phr": -4,
    "lyd": -5,
    "mix": -7,
    "aeo": 3,
    "loc": 1,
}
"""Dict. mapping mode names to chromatic step deltas (relative to Ionian)."""

# # TODO: probably could generate these instead
# MODE_CHROMATIC_SCALE_DEGREES = {
#     # major
#     "lyd": ["1", "#1", "2", "b3", "3", "b4", "4", "5", "b6", "6", "b7", "7"],
#     "maj": ["1", "#1", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7"],
#     "mix": ["1", "#1", "2", "b3", "3", "4", "#4", "5", "b6", "6", "7", "#7"],
#     # minor
#     "dor": ["1", "#1", "2", "3", "#3", "4", "#4", "5", "b6", "6", "7", "#7"],
#     "min": ["1", "#1", "2", "3", "#3", "4", "#4", "5", "6", "#6", "7", "#7"],
#     "phr": ["1", "2", "#2", "3", "#3", "4", "#4", "5", "6", "#6", "7", "#7"],
#     # diminished
#     "loc": ["1", "2", "#2", "3", "#3", "4", "5", "5#", "6", "#6", "7", "#7"],
# }

MAJOR_CHROMATIC_SCALE_DEGREES = ["1", "b2", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7"]
# _MAJOR_CHROMATIC_SCALE_DEGREE_STEPS = [2, 1, 2, 2, 1, 2, 2]

# https://en.wikipedia.org/wiki/Solf%C3%A8ge#Movable_do_solf%C3%A8ge
CHROMATIC_SOLFEGE = ["Do", "Di", "Re", "Me", "Mi", "Fa", "Fi", "Sol", "Le", "La", "Te", "Ti"]
CHROMATIC_SOLFEGE_ALL = [
    ("Do",),
    ("Di", "Ra"),
    ("Re",),
    ("Ri", "Me"),
    ("Mi",),
    ("Fa",),
    ("Fi", "Se"),
    ("Sol",),
    ("Si", "Le"),
    ("La",),
    ("Li", "Te"),
    ("Ti",),
]
"""Where there are two options, a 2-tuple with the raised one first and then the lowered one."""

SOLFEGE_NAT = [t[0] for t in CHROMATIC_SOLFEGE_ALL if len(t) == 1]

# CHROMATIC_SCALE_DEGREE = ["1", "#1", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7"]
CHROMATIC_SCALE_DEGREE = ["1", "b2", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7"]

CMAJ_LETTERS = ["C", "D", "E", "F", "G", "A", "B"]


def _mode_is_equiv(m1: str, m2: str) -> bool:
    """Compare modes based on their integer values,
    allowing major == ionian and minor == aeolian.
    """
    return MODE_VALUES[m1] == MODE_VALUES[m2]


CHROMATIC_VALUES_IN_MAJOR = [0, 2, 4, 5, 7, 9, 11]

MODE_SCALE_DEGREE = {
    "maj": 1,
    "min": 6,
    #
    "ion": 1,
    "dor": 2,
    "phr": 3,
    "lyd": 4,
    "mix": 5,
    "aeo": 6,
    "loc": 7,
}
"""Scale degree of the major scale that we would set as the tonic to get the given mode.
For example, if we start on A within the context of the C major scale (scale degree 6),
we get A minor.
"""


def _scale_chromatic_values(mode: str) -> List[int]:
    """The 7 integer chromatic values that make of the scale."""
    mode = _validate_and_normalize_mode_name(mode)
    i = MODE_SCALE_DEGREE[mode]
    i0 = i - 1

    vs_wrt_major = CHROMATIC_VALUES_IN_MAJOR[i0:] + CHROMATIC_VALUES_IN_MAJOR[:i0]
    dv = MODE_VALUES[mode]

    return [(v + dv) % 12 for v in vs_wrt_major]


def _mode_chromatic_scale_degrees(mode: str, *, acc_format: str = "#") -> List[str]:
    """For a given mode, scale degree representations for all 12 chromatic values."""
    valid_acc_formats = ["#", "b", "#/b", "b/#"]
    if acc_format not in valid_acc_formats:
        raise ValueError(
            f"invalid `acc_format` {acc_format!r}. "
            f"Valid options are: {', '.join(repr(s) for s in valid_acc_formats)}"
        )

    scvs = _scale_chromatic_values(_validate_and_normalize_mode_name(mode))
    csds = ["" for _ in range(12)]

    # First fill non-accidentals
    for i, v in enumerate(scvs, start=1):
        csds[v] = str(i)

    assert csds[0] == "1"

    # Now fill in the rest
    for i, s in enumerate(csds):
        if s:
            continue

        s_s = f"#{csds[i-1]}"
        s_f = f"b{csds[(i+1)%12]}"

        if acc_format == "#":
            s_ = s_s
        elif acc_format == "b":
            s_ = s_f
        elif acc_format == "#/b":
            s_ = f"{s_s}/{s_f}"
        elif acc_format == "b/#":
            s_ = f"{s_f}/{s_s}"

        csds[i] = s_

    return csds


def _mode_scale_degrees_wrt_major(mode: str) -> List[str]:
    """ASCII scale degrees for a certain mode,
    referenced to major using #/b.
    """
    sds = [MAJOR_CHROMATIC_SCALE_DEGREES[i] for i in _scale_chromatic_values(mode)]
    if mode == "loc":
        # Express Locrian in flats: #4 -> b5
        sds[4] = "b5"
    return sds


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
        self,
        name: Optional[str] = None,
        *,
        root: Optional[str] = None,
        mode: Optional[str] = None,
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
            # Handle occasional `K:` line used to indicate default key (C) and tune start
            if name == "":
                name = "C"
            self.root, self._mode = Key.parse_key(name)
        else:
            assert root is not None and mode is not None, "pass either `name` or `root`+`mode`"
            self.root = PitchClass.from_name(root)
            self._mode = _validate_and_normalize_mode_name(mode)

    @property
    def mode(self) -> str:
        return MODE_ABBR_TO_FULL[self._mode].capitalize()

    @staticmethod
    def parse_key(key: str) -> Tuple[PitchClass, str]:
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
            mode = _validate_and_normalize_mode_name(mode)
        except ValueError:
            raise ValueError("Unrecognized mode specification '{mode}' from key '{key}'")

        return PitchClass.from_name(base + acc), mode
        # TODO: probably should either return a Key or be private / maybe outside class

    @property
    def key_signature(self) -> List[str]:  # TODO: maybe change name
        """
        List of accidentals that should be displayed in the key
        signature for the given key description.
        """
        # Determine number of sharps/flats for this key by first converting
        # to Ionian, then doing the key lookup.
        key = self.relative_major
        num_acc = IONIAN_SHARPFLAT_COUNT[key.root.name]

        sig = []
        # Sharps or flats?
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

    def relative(self, mode: str, *, match_acc: bool = False) -> "Key":
        mode = _validate_and_normalize_mode_name(mode)
        key, mode0 = self.root, self._mode

        rel = MODE_VALUES[mode0] - MODE_VALUES[mode]
        root = PitchClass((key.value + rel) % 12)

        root_es = root.equivalent_sharp
        root_ef = root.equivalent_flat

        if match_acc:
            # Select flat or sharp to match the current key name

            # TODO: PitchClass from value with acc option?
            if "#" in key.name:
                if root_es.acc == "#":  # single sharp used
                    root_name = root_es.name
            elif "b" in key.name:
                if root_ef.acc == "b":  # single flat used
                    root_name = root_ef.name
            else:
                root_name = root.name

        else:
            # Use the letter that it should be in the scale
            sd0 = MODE_SCALE_DEGREE[mode0]
            sd = MODE_SCALE_DEGREE[mode]
            inn = (CMAJ_LETTERS.index(self.root.nat) + (sd - sd0)) % 7
            new_nat = CMAJ_LETTERS[inn]

            # We can't use `.accidentals` since it uses `.relative_major`
            # (causes stack overflow)
            if root.nat != new_nat:
                if root_es.nat == new_nat:
                    root_name = root_es.name
                elif root_ef.nat == new_nat:
                    root_name = root_ef.name
                else:
                    raise Exception
            else:
                root_name = root.name

        return Key(root=root_name, mode=mode)

    @property
    def relative_major(self) -> "Key":
        return self.relative("major")

    @property
    def relative_minor(self) -> "Key":
        return self.relative("minor")

    @property
    def _letters(self) -> List[str]:
        """Letters (natural note names) of the scale.
        Only depends on root.
        """
        ir = CMAJ_LETTERS.index(self.root.nat)
        return CMAJ_LETTERS[ir:] + CMAJ_LETTERS[:ir]

    @property
    def scale(self) -> List[PitchClass]:
        """Notes (pitch classes) of the scale."""
        nats = self._letters
        notes = [n + self.accidentals.get(n, "") for n in nats]
        return [PitchClass.from_name(n) for n in notes]

    def print_scale(self) -> None:
        print(" ".join(f"{str(pc):2}" for pc in self.scale))

    @property
    def scale_degrees_wrt_major(self) -> List[str]:
        """Scale degrees of the mode's scale, with #/b
        as compared to the major scale with the same root.
        """
        return _mode_scale_degrees_wrt_major(self._mode)

    def print_scale_degrees_wrt_major(self, **kwargs) -> None:
        print(" ".join(f"{sd:2}" for sd in self.scale_degrees_wrt_major))

    @property
    def scale_chromatic_values(self) -> List[int]:
        """Integer chromatic values that make up the scale,
        relative to root.
        Only depends on mode.
        """
        return _scale_chromatic_values(self._mode)

    def print_scale_chromatic_values(self) -> None:
        print(" ".join(f"{i:2}" for i in self.scale_chromatic_values))

    @property
    def intervals(self) -> List[str]:
        """List of the intervals that compose the scale.
        Only depends on mode."""
        return _scale_intervals(self.scale_chromatic_values)

    def print_intervals(self, *, fmt="WH") -> None:
        if fmt == "WH":
            print(" ".join(i for i in self.intervals))
        elif fmt == "-":
            m = {"W": "--", "H": "-"}
            print("|" + "|".join(m.get(i, "?") for i in self.intervals))

    def __str__(self):
        return f"{self.root.name}{self._mode}"

    def __repr__(self):
        return f"Key(root={self.root.name}, mode={self.mode!r})"

    def __eq__(self, other):
        if isinstance(other, Key):
            return self.root == other.root and _mode_is_equiv(self._mode, other._mode)
        else:
            return NotImplemented


class ContextualizedPitchClass(PitchClass):
    """A pitch class that knows how it fits in a scale (key/mode),
    giving context for expression of scale degrees and note names.
    """

    def __init__(self, value, key: Union[Key, str] = "C"):
        """
        value
            Integer chromatic value.
        key
            Desired key context.
        """
        if isinstance(key, str):
            key = Key(key)

        super().__init__(value)

        self.key = key

    def __repr__(self):
        return f"{type(self).__name__}(value={self.value}, key={str(self.key)})"
