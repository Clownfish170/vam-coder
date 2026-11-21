from mid import bias
from top import push


def test_top_fixed():
    assert push(3) == 10


def test_mid_regression():
    assert bias(3) == 10
    assert bias(-2) == 0
