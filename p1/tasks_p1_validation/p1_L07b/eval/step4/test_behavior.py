from leaf import meanish, mean_sum
from top import serve_s


def test_sum_empty():
    assert mean_sum([]) == -1
def test_sum_values():
    assert mean_sum([2, 3]) == 13


def test_top_regression():
    assert serve_s(3) == 10
