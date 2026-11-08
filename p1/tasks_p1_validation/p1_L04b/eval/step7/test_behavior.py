from mid import align
from top import flush
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        align(3, -1)


def test_chain_regression():
    assert align(3, 2) == 12
    assert flush(3) == 10
