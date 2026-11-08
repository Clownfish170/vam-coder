from leaf import grow
from mid import shift, shift_x2


def test_mid_x2():
    assert shift_x2(3) == 18
    assert shift_x2(-2) == -2


def test_mid_base():
    assert shift(3) == 10
