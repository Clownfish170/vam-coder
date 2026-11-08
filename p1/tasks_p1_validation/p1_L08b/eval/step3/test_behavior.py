from mid import gate
from top import dispatch


def test_top_fixed():
    assert dispatch(3) == 10


def test_mid_regression():
    assert gate(3) == 10
    assert gate(-2) == 0
