from leaf import pad_sum, pad
from top import flush


def test_sum_any_negative():
    assert pad_sum([2, -1]) == -1
    assert pad_sum([2, 3]) == 13
    assert pad_sum([]) == -1


def test_top_regression():
    assert flush(3) == 10
