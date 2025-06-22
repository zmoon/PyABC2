"""
Test the key module
"""
from itertools import product

import pytest

from pyabc2.key import (
    CMAJ_LETTERS,
    MODE_VALUES,
    Key,
    _mode_chromatic_scale_degrees,
    _scale_intervals,
)


def many_possible_key_name_inputs():
    # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/tests/test_keys.py#L11-L42
    from itertools import product

    from pyabc2.key import MODE_VALUES
    from pyabc2.pitch import NICE_C_CHROMATIC_NOTES

    # Base list of keys as C chromatic notes
    keys = NICE_C_CHROMATIC_NOTES

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


def test_default_key():
    k = Key("")
    assert k.tonic.name == "C"


def test_parse_key_invalid_base_fails():
    with pytest.raises(ValueError, match="Invalid key specification"):
        Key.parse_key("X")


def test_parse_key_invalid_mode_fails():
    with pytest.raises(ValueError, match="Unrecognized mode specification"):
        with pytest.warns(UserWarning, match="extra info"):
            Key.parse_key("Bad mode + extras warning")


def test_sharp_key_sig():
    k = Key("Amaj")
    assert k.key_signature == ["F#", "C#", "G#"]
    for n in "FCG":
        assert k.accidentals[n] == "#"


def test_flat_key_sig():
    k = Key("Eb")
    assert k.key_signature == ["Bb", "Eb", "Ab"]
    for n in "BEA":
        assert k.accidentals[n] == "b"


def test_relatives():
    Am = Key("Am")
    C = Key("C")
    assert Am.relative("ionian") == Am.relative_major == C
    assert C.relative("aeolian") == C.relative_minor == Am
    assert Key("Ador").relative_major == Key("G")

    assert Am.relative("major", match_acc=True) == C
    assert Key("Cb").relative("dorian") == Key("Dbdor")
    assert Key("Cb").relative("dorian", match_acc=True) == Key("Dbdor")
    assert Key("C#").relative("dorian", match_acc=True) == Key("D#dor")
    assert Key("C#").relative("dorian") == Key("D#dor")


@pytest.mark.parametrize(
    ("mode", "acc_format"), [(m, a) for m, a in product(MODE_VALUES, ["#", "b", "#/b", "b/#"])]
)
def test_mode_chromatic_scale_degrees(mode, acc_format):
    csds = _mode_chromatic_scale_degrees(mode, acc_fmt=acc_format)
    assert len(csds) == 12
    assert all(len(s) in [1, 2, 5] and s[-1:-2:-1] in "1234567" for s in csds)


def test_invalid_mode_chromatic_scale_degrees_bad_mode():
    with pytest.raises(ValueError, match="invalid mode name"):
        _mode_chromatic_scale_degrees("invalid")


def test_invalid_mode_chromatic_scale_degrees_bad_acc_fmt():
    with pytest.raises(ValueError, match="invalid `acc_format`"):
        _mode_chromatic_scale_degrees("ionian", acc_fmt="invalid")


@pytest.mark.parametrize("mode", MODE_VALUES)
def test_mode_scale_degrees_wrt_major(mode):
    # They should be the same no matter the tonic is.
    from pyabc2.key import IONIAN_SHARPFLAT_COUNT

    tonics = list(IONIAN_SHARPFLAT_COUNT)

    sdss = [Key(f"{t}{mode}").scale_degrees_wrt_major for t in tonics]

    assert all(sds == sdss[0] for sds in sdss)


@pytest.mark.parametrize("nat", CMAJ_LETTERS)
def test_key_letters(nat):
    natmaj = Key(nat)
    assert all(
        Key(tonic=r, mode=m)._letters == natmaj._letters
        for (r, m) in product([f"{nat}b", nat, f"{nat}#"], MODE_VALUES)
    )


@pytest.mark.parametrize("nat", CMAJ_LETTERS)
def test_major_key_intervals(nat):
    assert "".join(Key(nat).intervals) == "WWHWWWH"


def test_key_printers_succeed():
    k = Key("C")
    for n in dir(k):
        if n.startswith("print_"):
            getattr(k, n)()


def test_scvs_consistency():
    key = Key("C")
    scvs0 = key.scale_chromatic_values
    scvs = [pc.value_in(key) for pc in key.scale]
    assert scvs0 == scvs


def test_str():
    assert str(Key("C")) == "Cmaj"


def test_repr():
    assert repr(Key("C")) == "Key(tonic=C, mode='Major')"


def test_inequality():
    assert Key("C") != "this is not a Key"


def test_whole_tone_scale_intervals_fails():
    with pytest.raises(ValueError, match=r"expected 7 values, got 6"):
        _scale_intervals([0, 2, 4, 6, 8, 10])


def test_nonzero_start_fails():
    with pytest.raises(ValueError, match=r"first value should be 0"):
        _scale_intervals([1] * 7)


def test_beyond_octave_fails():
    with pytest.raises(ValueError, match=r"last value should be < 12"):
        _scale_intervals([0, 2, 4, 5, 7, 9, 13])


def test_scale_with_large_interval_fails():
    with pytest.raises(ValueError, match=r"strange interval \(not W/H\)"):
        _scale_intervals([0, 2, 3, 5, 6, 9, 10])


def test_print_scale(capsys):
    Key("C").print_scale()
    output = capsys.readouterr().out
    assert output == "C  D  E  F  G  A  B \n"


def test_print_scale_degrees_wrt_major(capsys):
    Key("C").print_scale_degrees_wrt_major()
    output = capsys.readouterr().out
    assert output == "1  2  3  4  5  6  7 \n"


def test_print_chromatic_scale_degrees(capsys):
    Key("C").print_chromatic_scale_degrees()
    output = capsys.readouterr().out
    assert output == "1  #1 2  #2 3  4  #4 5  #5 6  #6 7 \n"


def test_print_scale_chromatic_values(capsys):
    Key("C").print_scale_chromatic_values()
    output = capsys.readouterr().out
    assert output == "0  2  4  5  7  9  11\n"


def test_print_intervals_wh(capsys):
    Key("C").print_intervals()
    output = capsys.readouterr().out
    assert output == "W W H W W W H\n"


def test_print_intervals_dash(capsys):
    Key("C").print_intervals(fmt="-")
    output = capsys.readouterr().out
    assert output == "|--|--|-|--|--|--|-\n"
