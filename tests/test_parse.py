"""
Test ABC parsing
"""
from pyabc2.parse import Tune

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
