import engine


def test_apply_uses_constant():
    assert engine.apply_weight(2) == 6
    assert engine.apply_weight(5) == 15


def test_check_regression():
    assert engine.positive(-1) is False
