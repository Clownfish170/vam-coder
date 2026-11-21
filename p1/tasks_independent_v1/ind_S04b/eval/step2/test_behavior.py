import rounding


def test_round2():
    assert rounding.round2(2.225) == 2.23


def test_round2_plain():
    assert rounding.round2(1.5) == 1.5


def test_round1_regression():
    assert rounding.round1(2.25) == 2.3
    assert rounding.round1(-2.25) == -2.3
