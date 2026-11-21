from leaf import norm
from mid import tune, tune_x2


def test_mid_x2():
    assert tune_x2(3) == 36
    assert tune_x2(-2) == -4


def test_mid_base():
    assert tune(3) == 10
