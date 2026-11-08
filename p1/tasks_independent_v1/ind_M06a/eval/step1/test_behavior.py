import expr


def test_split_ops():
    assert expr.tokenize("1+2") == ["1", "+", "2"]
    assert expr.tokenize("3-4") == ["3", "-", "4"]


def test_spaced_still_works():
    assert expr.tokenize("1 + 2") == ["1", "+", "2"]


def test_evaluate_regression():
    assert expr.evaluate("1 2 3") == 1
