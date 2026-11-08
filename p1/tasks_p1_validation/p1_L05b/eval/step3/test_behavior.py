from mid import step
from top import drive


def test_top_fixed():
    assert drive(3) == 10


def test_mid_regression():
    assert step(3) == 10
    assert step(-2) == 0
