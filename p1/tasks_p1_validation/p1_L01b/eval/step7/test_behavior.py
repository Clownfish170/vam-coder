from mid import adjust
from top import serve
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        adjust(3, -1)


def test_chain_regression():
    assert adjust(3, 2) == 12
    assert serve(3) == 10
