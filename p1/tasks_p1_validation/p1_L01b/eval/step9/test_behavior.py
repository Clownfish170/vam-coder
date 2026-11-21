from leaf import total, shape
from top import serve


def test_sum_any_negative():
    assert total([2, -1]) == -1
    assert total([2, 3]) == 13
    assert total([]) == -1


def test_top_regression():
    assert serve(3) == 10
