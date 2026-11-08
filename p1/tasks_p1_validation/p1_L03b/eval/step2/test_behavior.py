from leaf import embed
from mid import bias, bias_x2


def test_mid_x2():
    assert bias_x2(3) == 45
    assert bias_x2(-2) == -5


def test_mid_base():
    assert bias(3) == 10
