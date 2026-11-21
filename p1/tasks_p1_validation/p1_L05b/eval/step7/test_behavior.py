from mid import step
from top import drive
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        step(3, -1)


def test_chain_regression():
    assert step(3, 2) == 12
    assert drive(3) == 10
