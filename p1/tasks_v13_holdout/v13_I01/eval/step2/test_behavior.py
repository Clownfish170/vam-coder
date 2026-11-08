import engine
from curves_body import calibrate


def test_quote_sum():
    assert engine.quote_sum([0, 1, 2]) == calibrate(0) + calibrate(1) + calibrate(2)


def test_quote_sum_empty():
    assert engine.quote_sum([]) == 0


def test_quote_regression():
    assert engine.quote(9) == calibrate(9)
