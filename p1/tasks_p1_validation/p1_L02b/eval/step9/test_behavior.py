from leaf import sum_all, norm
from top import handle


def test_sum_any_negative():
    assert sum_all([2, -1]) == -1
    assert sum_all([2, 3]) == 13
    assert sum_all([]) == -1


def test_top_regression():
    assert handle(3) == 10
