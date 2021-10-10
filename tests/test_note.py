"""
Test the pitch and note modules
"""
import pytest

from pyabc2.key import Key
from pyabc2.note import Note
from pyabc2.pitch import (
    Pitch,
    PitchClass,
    SignedInterval,
    SimpleInterval,
    _to_roman,
    pitch_class_value,
)

C = Key("Cmaj")


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
    assert pitch_class_value(name) == expected_value


@pytest.mark.parametrize(
    ("name", "expected_value"),
    [
        ("B##", 13),
        ("Cb", -1),
        ("Dbbb", -1),
    ],
)
def test_pitch_value_acc_outside_octave(name, expected_value):
    with pytest.warns(UserWarning):
        value = pitch_class_value(name)
    assert value == expected_value

    pitch_class_value(name, mod=True)  # no warning


@pytest.mark.parametrize("p", ["C", "Dbb"])
def test_C_variants(p):
    assert PitchClass.from_name("C") == PitchClass.from_name(p)


def test_equiv_sharp_flat():
    p0 = PitchClass.from_name("D")
    assert p0.equivalent_flat == PitchClass.from_name("Ebb")
    assert p0.equivalent_sharp == PitchClass.from_name("C##")


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
    assert p.class_name == expected_new_name

    pc0 = PitchClass.from_name("C")
    pc = pc0 + d
    assert pc.name == expected_new_name


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
    p0 = PitchClass.from_name("C")
    p = p0 - d
    assert p.name == expected_new_name

    pc0 = PitchClass.from_name("C")
    pc = pc0 - d
    assert pc.name == expected_new_name


def test_eq():
    assert Pitch.from_name("C4") == Pitch.from_class_value(0, 4) == Pitch(48)
    assert Pitch.from_class_value(0, 4) != Pitch.from_class_value(0, 3)


def test_nice_names_from_values():
    ps = [PitchClass(i) for i in range(6)]
    assert [p.name for p in ps] == ["C", "C#", "D", "Eb", "E", "F"]


@pytest.mark.parametrize(("note", "octave", "expected_freq"), [("C", 4, 261.6256), ("A", 4, 440.0)])
def test_etf(note, octave, expected_freq):
    p = Pitch.from_name(f"{note}{octave}")
    assert p.equal_temperament_frequency == p.etf == pytest.approx(expected_freq)


def test_pitch_from_etf():
    Pitch.from_etf(440) == Pitch.from_name("A4")


def test_pitch_class_to_pitch():
    C4 = Pitch.from_class_value(0, 4)

    assert PitchClass.from_name("C").to_pitch(4) == C4


def test_pitch_to_pitch_class():
    D = PitchClass.from_name("D")

    assert Pitch(50).to_pitch_class() == D


# TODO: test add/mul Pitch(Class)


@pytest.mark.parametrize(
    ("abc", "expected_str_rep"),
    [
        # Octave
        ("C", "C4_1/8"),
        ("C,,", "C2_1/8"),
        ("C,,'", "C3_1/8"),
        #
        # Accidentals
        ("_B,2,", "Bb3_1/4"),
        ("^f", "F#5_1/8"),
        ("^^f',,3", "F##4_3/8"),
        #
        # Relative duration
        ("C/", "C4_1/16"),
        ("C//", "C4_1/32"),
        ("C/3", "C4_1/24"),
        ("C3/", "C4_3/16"),  # dotted eigth note
        ("C3/2", "C4_3/16"),
    ],
)
def test_note_from_abc(abc, expected_str_rep):
    assert str(Note.from_abc(abc)) == expected_str_rep


def test_note_from_abc_key():
    assert Note.from_abc("F", key=Key("D")) == Note.from_abc("^F")


def test_note_to_from_abc_consistency():
    n = Note(49, duration=2)
    assert Note.from_abc(n.to_abc()) == n

    assert Note.from_abc(n.to_abc(key=Key("C#")), key=Key("C#")) == n


@pytest.mark.parametrize(
    ("v", "expected_name"),
    [
        (0, "P1"),
        (2, "M2"),
        (10, "m7"),
        (12, "P8"),
        (24, "P8"),
    ],
)
def test_simple_interval_name(v, expected_name):
    if 0 <= v <= 12:
        assert SimpleInterval(v).name == expected_name
    else:
        with pytest.warns(UserWarning):
            assert SimpleInterval(v).name == expected_name


@pytest.mark.parametrize(
    ("v", "expected_name"),
    [
        (0, "P1"),
        (2, "M2"),
        (3, "m3"),
        (15, "P8+m3"),
        (27, "2(P8)+m3"),
        (-27, "-[2(P8)+m3]"),
    ],
)
def test_signed_interval_name(v, expected_name):
    assert SignedInterval(v).name == expected_name


def test_interval_returned_from_pitch_sub():
    assert Pitch(50) - Pitch(40) == SignedInterval(10)
    assert Pitch(40) - Pitch(50) == SignedInterval(-10)
    assert PitchClass(7) - PitchClass(0) == SimpleInterval(7)
    with pytest.warns(UserWarning):
        assert PitchClass(0) - PitchClass(7) == SimpleInterval(7)


def test_add_interval_to_pitch():
    assert Pitch(40) + SignedInterval(-10) == Pitch(30)
    assert PitchClass(0) + SimpleInterval(5) == PitchClass(5)


def test_simple_interval_inverse():
    m3 = SimpleInterval.from_name("m3")
    assert m3.value == 3
    assert m3.inverse.name == "M6"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("C", 1),
        ("D", 2),
        ("B", 7),
        ("C#", -999),
    ],
)
def test_scale_degree_int_in_C(name, expected):
    pc = PitchClass.from_name(name)
    if expected == -999:
        with pytest.raises(ValueError):
            assert pc.scale_degree_int_in(C) == expected
    else:
        assert pc.scale_degree_int_in(C) == expected


@pytest.mark.parametrize(
    ("i", "expected"),
    [
        (1, "I"),
        (3, "III"),
        (4, "IV"),
        (9, "IX"),
        (15, "XV"),
        (20, "XX"),
    ],
)
def test_to_roman(i, expected):
    assert _to_roman(i) == expected


def test_scale_degree_in_C_formats():
    pc = PitchClass.from_name("C#")
    assert pc.scale_degree_in(C) == "#1"
    assert pc.scale_degree_in(C, acc_fmt="unicode") == "♯1"
    assert pc.scale_degree_in(C, num_fmt="roman", acc_fmt="unicode") == "♯I"

    with pytest.raises(ValueError):
        pc.scale_degree_in(C, num_fmt="asdf")

    with pytest.raises(ValueError):
        pc.scale_degree_in(C, acc_fmt="asdf")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("C#", "#1"),
        ("Db", "b2"),
        ("C##", "##1"),
    ],
)
def test_scale_degree_in_C(name, expected):
    pc = PitchClass.from_name(name)
    assert pc.scale_degree_in(C) == expected


def test_scale_degree_in_nonC():
    G = Key("G")
    sd7 = PitchClass.from_name("F#")
    sd7_enh = PitchClass(6)
    assert sd7.scale_degree_in(G) == sd7_enh.scale_degree_in(G) == "7"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "1"),
        (1, "#1/b2"),
        (2, "2"),
        (10, "#6/b7"),
        (11, "7"),
    ],
)
def test_scale_degree_in_C_enh(value, expected):
    pc = PitchClass(value)
    assert pc.scale_degree_in(C) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("C", "Do"),
        ("C#", "Di"),
        ("Cb", -999),
        ("Fb", -999),  # no b4
        ("G#", "Si"),
        ("G##", -999),
        ("D", "Re"),
        ("B", "Ti"),
        ("Bb", "Te"),
        ("B#", -999),
    ],
)
def test_solfege_in_C(name, expected):
    pc = PitchClass.from_name(name)

    if expected == -999:
        with pytest.raises(ValueError):
            assert pc.solfege_in(C) == expected
    else:
        assert pc.solfege_in(C) == expected


def test_solfege_in_nonC():
    G = Key("G")
    sd7 = PitchClass.from_name("F#")
    sd7_enh = PitchClass(6)
    assert sd7.solfege_in(G) == sd7_enh.solfege_in(G) == "Ti"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "Do"),
        (1, "Di/Ra"),
        (2, "Re"),
        (10, "Li/Te"),
        (11, "Ti"),
    ],
)
def test_solfege_in_C_enh(value, expected):
    pc = PitchClass(value)
    assert pc.solfege_in(C) == expected


def test_note_name_preservation():
    """When converting to/from note classes."""

    pc = PitchClass.from_name("Db")
    cv1 = PitchClass(1)
    assert pc == cv1
    assert cv1.name == "C#"

    # PC -> P -> N
    p = pc.to_pitch(4)
    assert pc.name == p.class_name == p.to_note().class_name == "Db"

    # P -> PC
    p = Pitch.from_name("Db4")
    assert p.name == "Db4"
    assert p.class_name == p.to_pitch_class().name == "Db"

    # PC <- P
    assert PitchClass.from_pitch(p).name == "Db"

    # P <- PC
    assert Pitch.from_pitch_class(pc, 4).class_name == "Db"

    # N -> P
    n = Note.from_abc("_D")
    assert n.name == "Db4"
    assert str(n) == "Db4_1/8"
    assert n.to_pitch().class_name == "Db"
    assert n.to_pitch().name == "Db4"

    # N -> PC
    assert n.to_pitch_class().name == "Db"

    # N <- P
    p = Pitch.from_name("Db4")
    assert Note.from_pitch(p).class_name == "Db"
