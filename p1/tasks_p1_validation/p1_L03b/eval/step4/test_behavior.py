from leaf import embed, embed_sum
from top import push


def test_sum_empty():
    assert embed_sum([]) == -1
def test_sum_values():
    assert embed_sum([2, 3]) == 13


def test_top_regression():
    assert push(3) == 10
