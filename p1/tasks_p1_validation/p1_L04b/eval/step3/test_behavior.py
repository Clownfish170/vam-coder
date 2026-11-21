from mid import align
from top import flush


def test_top_fixed():
    assert flush(3) == 10


def test_mid_regression():
    assert align(3) == 10
    assert align(-2) == 0
