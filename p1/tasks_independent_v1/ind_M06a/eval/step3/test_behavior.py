import expr


def test_sub():
    assert expr.evaluate("5-2") == 3
    assert expr.evaluate("8 - 3") == 5


def test_add_regression():
    assert expr.evaluate("1+2") == 3


def test_mixed_left_to_right():
    assert expr.evaluate("9-3+1") == 7
