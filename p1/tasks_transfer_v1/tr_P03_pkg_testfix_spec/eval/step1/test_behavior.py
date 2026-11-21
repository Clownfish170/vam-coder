from packaging.specifiers import SpecifierSet
from packaging.version import Version

def test_contains_in_range():
    s = SpecifierSet(">=1.0,<2.0")
    assert Version("1.5") in s

def test_excludes_out_of_range():
    s = SpecifierSet(">=1.0,<2.0")
    assert Version("2.0") not in s
