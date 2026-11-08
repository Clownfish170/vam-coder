from leaf import pad
from mid import align, align_x2


def test_mid_x2():
    assert align_x2(3) == 18
    assert align_x2(-2) == -2


def test_mid_base():
    assert align(3) == 10
