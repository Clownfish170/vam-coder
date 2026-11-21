import engine


def test_apply_uses_constant():
    assert engine.apply_margin(2) == 16
    assert engine.apply_margin(5) == 40


def test_check_regression():
    assert engine.positive(-1) is False
