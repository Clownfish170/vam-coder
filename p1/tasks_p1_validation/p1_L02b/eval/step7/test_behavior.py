from mid import tune
from top import handle
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        tune(3, -1)


def test_chain_regression():
    assert tune(3, 2) == 12
    assert handle(3) == 10
