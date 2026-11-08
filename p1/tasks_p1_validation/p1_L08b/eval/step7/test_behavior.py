from mid import gate
from top import dispatch
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        gate(3, -1)


def test_chain_regression():
    assert gate(3, 2) == 12
    assert dispatch(3) == 10
