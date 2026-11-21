import engine


def test_pair():
    assert engine.margin_pair(1, 2) == 8 + 16


def test_apply_regression():
    assert engine.apply_margin(3) == 24


def test_check_regression():
    assert engine.positive(0) is False
