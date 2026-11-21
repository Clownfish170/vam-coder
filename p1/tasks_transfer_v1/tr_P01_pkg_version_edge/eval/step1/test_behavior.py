import pytest
from packaging.version import Version, InvalidVersion

def test_trailing_dot_rejected():
    with pytest.raises(InvalidVersion):
        Version("1.2.3.")

def test_valid_accept():
    assert str(Version("1.2.3")) == "1.2.3"
