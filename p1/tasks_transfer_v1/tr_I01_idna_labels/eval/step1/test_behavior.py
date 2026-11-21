import pytest
import idna

def test_double_dot_rejected():
    with pytest.raises(Exception):
        idna.encode("example..com")

def test_empty_label_rejected():
    with pytest.raises(Exception):
        idna.encode("a..b.com")
