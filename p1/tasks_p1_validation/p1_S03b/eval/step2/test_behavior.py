import engine


def test_pair():
    assert engine.weight_pair(1, 2) == 3 + 6


def test_apply_regression():
    assert engine.apply_weight(3) == 9


def test_check_regression():
    assert engine.positive(0) is False
