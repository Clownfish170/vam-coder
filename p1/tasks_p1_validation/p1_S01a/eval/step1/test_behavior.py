import core


def test_negative_zero():
    assert core.adjust(-2) == 0
    assert core.adjust(0) == 0


def test_positive_mult():
    assert core.adjust(3) == 15
    assert core.adjust(5) == 25


def test_base_unchanged():
    assert core.keep(7) == 7
