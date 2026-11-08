from leaf import render_n, render_sum
from top import dispatch


def test_sum_empty():
    assert render_sum([]) == -1
def test_sum_values():
    assert render_sum([2, 3]) == 13


def test_top_regression():
    assert dispatch(3) == 10
