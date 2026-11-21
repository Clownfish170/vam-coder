from leaf import norm, sum_all
from top import handle


def test_sum_empty():
    assert sum_all([]) == -1
def test_sum_values():
    assert sum_all([2, 3]) == 13


def test_top_regression():
    assert handle(3) == 10
