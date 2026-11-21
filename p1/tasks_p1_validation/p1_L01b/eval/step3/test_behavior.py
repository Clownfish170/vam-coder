from mid import adjust
from top import serve


def test_top_fixed():
    assert serve(3) == 10


def test_mid_regression():
    assert adjust(3) == 10
    assert adjust(-2) == 0
