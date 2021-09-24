"""
Test the key module
"""
import pytest

from pyabc2.key import Key


def many_possible_key_name_inputs():
    # https://github.com/campagnola/pyabc/blob/4c22a70a0f40ff82f608ffc19a1ca51a153f8c24/tests/test_keys.py#L11-L42
    from itertools import product

    from pyabc2.key import MODE_VALUES
    from pyabc2.note import CHROMATIC_NOTES

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
