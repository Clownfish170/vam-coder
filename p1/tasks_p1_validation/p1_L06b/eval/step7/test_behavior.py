from mid import shift
from top import relay
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        shift(3, -1)


def test_chain_regression():
    assert shift(3, 2) == 12
    assert relay(3) == 10
