from leaf import shape, total
from top import serve


def test_sum_empty():
    assert total([]) == -1
def test_sum_values():
    assert total([2, 3]) == 13


def test_top_regression():
    assert serve(3) == 10
