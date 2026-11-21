import expr


def test_multi_digit_tokenize():
    assert expr.tokenize("12+34") == ["12", "+", "34"]


def test_multi_digit_eval():
    assert expr.evaluate("12+34") == 46
    assert expr.evaluate("100 - 40") == 60


def test_single_digit_regression():
    assert expr.evaluate("5-2") == 3
