import engine


def test_apply_uses_constant():
    assert engine.apply_factor(2) == 10
    assert engine.apply_factor(5) == 25


def test_check_regression():
    assert engine.positive(-1) is False
