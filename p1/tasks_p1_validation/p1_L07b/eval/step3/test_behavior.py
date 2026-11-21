from mid import amp
from top import serve_s


def test_top_fixed():
    assert serve_s(3) == 10


def test_mid_regression():
    assert amp(3) == 10
    assert amp(-2) == 0
