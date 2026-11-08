from leaf import grow, grow_sum
from top import relay


def test_sum_empty():
    assert grow_sum([]) == -1
def test_sum_values():
    assert grow_sum([2, 3]) == 13


def test_top_regression():
    assert relay(3) == 10
