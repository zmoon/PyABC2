"""
Keys and their relations
"""
# https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/pyabc.py#L94
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



if __name__ == "__main__":
    print(PITCH_VALUES_WRT_C)
