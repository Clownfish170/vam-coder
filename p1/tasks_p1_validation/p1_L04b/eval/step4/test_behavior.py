from leaf import pad, pad_sum
from top import flush


def test_sum_empty():
    assert pad_sum([]) == -1
def test_sum_values():
    assert pad_sum([2, 3]) == 13


def test_top_regression():
    assert flush(3) == 10
