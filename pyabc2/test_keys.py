import pytest

from pyabc2.keys import Pitch


@pytest.mark.parametrize("p", ["C", "Dbb"])
def test_C_variants(p):
    assert Pitch("C") == Pitch(p)


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
    assert Pitch.pitch_value(name) == expected_value


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
        p = Pitch(name)
    assert p.value == expected_value


def test_equiv_sharp_flat():
    p0 = Pitch("D")
    assert p0.equivalent_flat == Pitch("Ebb")
    assert p0.equivalent_sharp == Pitch("C##")


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
    p0 = Pitch("C")
    p = p0 + d
    assert p.name == expected_new_name
    assert p.value == d


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
    p0 = Pitch("C")
    p = p0 - d
    assert p.name == expected_new_name
    assert p.value == -d


def test_eq():
    assert Pitch("C") == Pitch(0)
    assert Pitch("C", 4) != Pitch("C", 3)
    with pytest.raises(Exception):
        Pitch("C") == Pitch("C", 4)


def test_nice_names_from_values():
    ps = [Pitch(i) for i in range(6)]
    assert [p.name for p in ps] == ["C", "C#", "D", "Eb", "E", "F"]
