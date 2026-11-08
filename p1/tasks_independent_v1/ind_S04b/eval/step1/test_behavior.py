import rounding


def test_half_up():
    assert rounding.round1(2.25) == 2.3


def test_half_up_2():
    assert rounding.round1(2.35) == 2.4


def test_negative():
    assert rounding.round1(-2.25) == -2.3


def test_plain():
    assert rounding.round1(2.4) == 2.4
