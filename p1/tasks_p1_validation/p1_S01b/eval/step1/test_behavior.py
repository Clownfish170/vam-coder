import engine


def test_apply_uses_constant():
    assert engine.apply_rate(2) == 8
    assert engine.apply_rate(5) == 20


def test_check_regression():
    assert engine.positive(-1) is False
