from leaf import fold_sum, fold
from top import drive


def test_sum_any_negative():
    assert fold_sum([2, -1]) == -1
    assert fold_sum([2, 3]) == 13
    assert fold_sum([]) == -1


def test_top_regression():
    assert drive(3) == 10
