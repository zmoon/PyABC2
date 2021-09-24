"""
Test the note module
"""
import pytest

from pyabc2.note import Pitch, PitchClass, pitch_value


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


def test_pitch_class_to_pitch():
    C4 = Pitch(0, 4)

    assert PitchClass("C").to_pitch(4) == C4
    assert PitchClass("C", root="D").to_pitch(4) == C4


# TODO: test add/mul Pitch(Class)
