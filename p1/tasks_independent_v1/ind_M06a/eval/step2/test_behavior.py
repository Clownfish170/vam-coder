import expr


def test_add():
    assert expr.evaluate("1+2") == 3
    assert expr.evaluate("5 + 4") == 9


def test_single_number():
    assert expr.evaluate("7") == 7


def test_tokenize_regression():
    assert expr.tokenize("1+2") == ["1", "+", "2"]
