import engine


def test_pair():
    assert engine.factor_pair(1, 2) == 5 + 10


def test_apply_regression():
    assert engine.apply_factor(3) == 15


def test_check_regression():
    assert engine.positive(0) is False
