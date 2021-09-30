"""
Test ABC parsing
"""
from pyabc2.parse import INFO_FIELDS, Tune

# Norbeck version
# http://www.norbeck.nu/abc/display.asp?rhythm=jig&ref=12
abc_have_a_drink = """
X:12
T:Have a Drink with Me
R:jig
D:Patrick Street 1.
Z:id:hn-jig-12
M:6/8
K:G
BAG E2D|EGD EGA|BAB GED|EAA ABc|BAG E2D|EGD EGA|BAB GED|EGG G3:|
|:GBd e2d|dgd B2A|GBd edB|cea ~a3|bag age|ged ege|dBG ABc|BGG G3:|
""".strip()


def test_simple_tune():
    from pyabc2.key import Key

    t = Tune(abc_have_a_drink)

    assert t.title == "Have a Drink with Me"
    assert t.key == Key("G")
    assert t.type == "jig"


def test_info_fields():
    assert INFO_FIELDS["T"].name == "tune title"


def test_repeats_no_endings():
    abc = """
    T:?
    L:1
    M:4/4
    R:reel
    K:G
    G | A :|
    |: B | C :|
    """
    # TODO: maybe should be a warning if 2nd `:|` found but not a `|:`
    t = Tune(abc)

    assert " ".join(n.class_name for n in t.iter_notes()) == "G A G A B C B C"


def test_repeats_with_endings():
    abc = """
    T:?
    L:1
    M:4/4
    R:reel
    K:G
    G |1 A | A :|2 a | a ||
    |: B |1 C :|2 c ||
    """
    t = Tune(abc)

    assert " ".join(n.to_abc() for n in t.iter_notes()) == "G A A G a a B C B c"
