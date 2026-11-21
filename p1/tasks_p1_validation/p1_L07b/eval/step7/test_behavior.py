from mid import amp
from top import serve_s
import pytest


def test_boost_validation():
    with pytest.raises(ValueError):
        amp(3, -1)


def test_chain_regression():
    assert amp(3, 2) == 12
    assert serve_s(3) == 10
