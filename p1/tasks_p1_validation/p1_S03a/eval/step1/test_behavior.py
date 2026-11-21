import core


def test_negative_zero():
    assert core.norm_score(-2) == 0
    assert core.norm_score(0) == 0


def test_positive_mult():
    assert core.norm_score(3) == 12
    assert core.norm_score(5) == 20


def test_base_unchanged():
    assert core.clip_score(7) == 7
