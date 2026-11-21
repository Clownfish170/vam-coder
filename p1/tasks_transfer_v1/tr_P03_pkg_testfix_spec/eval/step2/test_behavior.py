from packaging.specifiers import SpecifierSet
from packaging.version import Version

def test_empty_set_contains_all():
    s = SpecifierSet("")
    assert Version("1.0") in s
    assert Version("99.0") in s

def test_range_still_works():
    s = SpecifierSet(">=1.0,<2.0")
    assert Version("1.5") in s
