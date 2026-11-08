import expr


def test_mul():
    assert expr.evaluate("3*4") == 12
    assert expr.evaluate("6 * 7") == 42


def test_chain():
    assert expr.evaluate("2+3*4") == 20


def test_multi_digit_regression():
    assert expr.evaluate("12+34") == 46
