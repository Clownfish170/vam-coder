from leaf import grow_sum, grow
from top import relay


def test_sum_any_negative():
    assert grow_sum([2, -1]) == -1
    assert grow_sum([2, 3]) == 13
    assert grow_sum([]) == -1


def test_top_regression():
    assert relay(3) == 10
