"""
Test the key module
"""

from itertools import product

import pytest

from pyabc2.key import CMAJ_LETTERS, MODE_VALUES, Key, _mode_chromatic_scale_degrees


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


def test_key_sig():
    k = Key("Amaj")
    assert k.key_signature == ["F#", "C#", "G#"]
    for n in "FCG":
        assert k.accidentals[n] == "#"


def test_relatives():
    Am = Key("Am")
    C = Key("C")
    assert Am.relative("ionian") == Am.relative_major == C
    assert C.relative("aeolian") == C.relative_minor == Am
    assert Key("Ador").relative_major == Key("G")


@pytest.mark.parametrize(
    ("mode", "acc_format"), [(m, a) for m, a in product(MODE_VALUES, ["#", "b", "#/b", "b/#"])]
)
def test_mode_chromatic_scale_degrees(mode, acc_format):
    csds = _mode_chromatic_scale_degrees(mode, acc_fmt=acc_format)
    assert len(csds) == 12
    assert all(len(s) in [1, 2, 5] and s[-1:-2:-1] in "1234567" for s in csds)


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
