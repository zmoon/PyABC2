"""
Test keys module
"""
import pytest

from pyabc2.keys import Key, Pitch, PitchClass, pitch_value


@pytest.mark.parametrize("p", ["C", "Dbb"])
def test_C_variants(p):
    assert PitchClass("C") == PitchClass(p)


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("C", 0),
        ("C#", 1),
        ("Db", 1),
        ("C###", 3),
        ("Eb", 3),
        ("Fbb", 3),
    ],
)
def test_pitch_value(name, expected_value):
    # using default root C
    assert pitch_value(name) == expected_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("B##", 13),
        ("Cb", -1),
        ("Dbbb", -1),
    ],
)
def test_acc_outside_octave(name, expected_value):
    with pytest.warns(UserWarning):
        value = pitch_value(name)
    assert value == expected_value


def test_equiv_sharp_flat():
    p0 = PitchClass("D")
    assert p0.equivalent_flat == PitchClass("Ebb")
    assert p0.equivalent_sharp == PitchClass("C##")


@pytest.mark.parametrize(
    ("d", "expected_new_name"),
    [
        (1, "C#"),
        (0, "C"),
        (-1, "B"),
        (12, "C"),
        (2, "D"),
        (5, "F"),
    ],
)
def test_add_int_to_C(d, expected_new_name):
    p0 = Pitch.from_name("C4")
    p = p0 + d
    assert p.name == expected_new_name
    # assert p.value == d


@pytest.mark.parametrize(
    ("d", "expected_new_name"),
    [
        (1, "B"),
        (0, "C"),
        (-1, "C#"),
        (12, "C"),
    ],
)
def test_sub_int_from_C(d, expected_new_name):
    p0 = Pitch.from_name("C4")
    p = p0 - d
    assert p.name == expected_new_name
    # assert p.value == -d


def test_eq():
    assert Pitch.from_name("C4") == Pitch(0, 4)
    assert Pitch(0, 4) != Pitch(0, 3)


def test_nice_names_from_values():
    ps = [PitchClass.from_value(i) for i in range(6)]
    assert [p.name for p in ps] == ["C", "C#", "D", "Eb", "E", "F"]


def many_possible_key_name_inputs():
    # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/tests/test_keys.py#L11-L42
    from itertools import product

    from pyabc2.keys import CHROMATIC_NOTES, MODE_VALUES

    # Base list of keys as C chromatic notes
    keys = CHROMATIC_NOTES

    # List of modes in sentence case
    modes = [m.capitalize() for m in MODE_VALUES]

    # Append upper and lower case versions of the above
    modes += [m.lower() for m in modes] + [m.upper() for m in modes]

    # Append truncated versions of the above
    modes += [m[:3] for m in modes]
    modes += ["m"]

    return [k + m for k, m in product(keys, modes)]


@pytest.mark.parametrize("key_name", many_possible_key_name_inputs())
def test_parse_key_basic_succeeds(key_name):
    # TODO: could create a shorter version with a few selected examples and mark this one as long
    # Attempt to create key using key string provided.
    Key(name=key_name)


def test_key_sig():
    k = Key("Amaj")
    assert k.key_signature == ["F#", "C#", "G#"]
    for n in "FCG":
        assert k.accidentals[n] == "#"


def test_relatives():
    Am = Key("Am")
    C = Key("C")
    assert Am.relative_ionian == Am.relative_major == C
    assert C.relative_aeolian == C.relative_minor == Am


@pytest.mark.parametrize(("note", "octave", "expected_freq"), [("C", 4, 261.6256), ("A", 4, 440.0)])
def test_etf(note, octave, expected_freq):
    p = Pitch.from_name(f"{note}{octave}")
    assert p.equal_temperament_frequency == p.etf == pytest.approx(expected_freq)


def test_pitch_from_etf():
    Pitch.from_etf(440) == Pitch.from_name("A4")


def test_root_changing():
    p0 = PitchClass("C")
    p = p0.with_root("Bb")
    assert p0.name == p.name, "only value should be changing"
    assert p.value == 2
