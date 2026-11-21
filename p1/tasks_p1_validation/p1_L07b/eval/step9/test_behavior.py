from leaf import mean_sum, meanish
from top import serve_s


def test_sum_any_negative():
    assert mean_sum([2, -1]) == -1
    assert mean_sum([2, 3]) == 13
    assert mean_sum([]) == -1


def test_top_regression():
    assert serve_s(3) == 10
