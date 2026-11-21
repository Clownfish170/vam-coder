from leaf import meanish
from mid import amp, amp_x2


def test_mid_x2():
    assert amp_x2(3) == 54
    assert amp_x2(-2) == -6


def test_mid_base():
    assert amp(3) == 10
