from leaf import shape
from mid import adjust, adjust_x2


def test_mid_x2():
    assert adjust_x2(3) == 27
    assert adjust_x2(-2) == -3


def test_mid_base():
    assert adjust(3) == 10
