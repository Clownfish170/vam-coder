from leaf import render_sum, render_n
from top import dispatch


def test_sum_any_negative():
    assert render_sum([2, -1]) == -1
    assert render_sum([2, 3]) == 13
    assert render_sum([]) == -1


def test_top_regression():
    assert dispatch(3) == 10
