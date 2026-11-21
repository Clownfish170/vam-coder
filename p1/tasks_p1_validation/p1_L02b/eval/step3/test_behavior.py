from mid import tune
from top import handle


def test_top_fixed():
    assert handle(3) == 10


def test_mid_regression():
    assert tune(3) == 10
    assert tune(-2) == 0
