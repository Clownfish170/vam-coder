import core


def test_negative_zero():
    assert core.scale_w(-2) == 0
    assert core.scale_w(0) == 0


def test_positive_mult():
    assert core.scale_w(3) == 18
    assert core.scale_w(5) == 30


def test_base_unchanged():
    assert core.raw_w(7) == 7
