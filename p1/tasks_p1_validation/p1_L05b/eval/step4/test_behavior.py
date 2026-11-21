from leaf import fold, fold_sum
from top import drive


def test_sum_empty():
    assert fold_sum([]) == -1
def test_sum_values():
    assert fold_sum([2, 3]) == 13


def test_top_regression():
    assert drive(3) == 10
