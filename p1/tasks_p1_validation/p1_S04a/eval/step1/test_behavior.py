import core


def test_negative_zero():
    assert core.tier_of(-2) == 0
    assert core.tier_of(0) == 0


def test_positive_mult():
    assert core.tier_of(3) == 21
    assert core.tier_of(5) == 35


def test_base_unchanged():
    assert core.plain(7) == 7
