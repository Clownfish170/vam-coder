from mid import bias
from top import push
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        bias(3, -1)


def test_chain_regression():
    assert bias(3, 2) == 12
    assert push(3) == 10
