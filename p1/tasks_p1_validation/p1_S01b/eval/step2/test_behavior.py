import engine


def test_pair():
    assert engine.apply_pair(1, 2) == 4 + 8


def test_apply_regression():
    assert engine.apply_rate(3) == 12


def test_check_regression():
    assert engine.positive(0) is False
