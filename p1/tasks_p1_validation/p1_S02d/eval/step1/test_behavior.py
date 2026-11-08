import pytest
from vault import Session


def test_positive_ok():
    a = Session(50)
    assert a.consume(20) == 30


def test_zero_raises():
    a = Session(50)
    with pytest.raises(ValueError):
        a.consume(0)


def test_negative_raises():
    a = Session(50)
    with pytest.raises(ValueError):
        a.consume(-5)
