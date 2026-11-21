from mid import shift
from top import relay


def test_top_fixed():
    assert relay(3) == 10


def test_mid_regression():
    assert shift(3) == 10
    assert shift(-2) == 0
