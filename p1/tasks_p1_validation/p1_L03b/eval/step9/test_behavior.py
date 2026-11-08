from leaf import embed_sum, embed
from top import push


def test_sum_any_negative():
    assert embed_sum([2, -1]) == -1
    assert embed_sum([2, 3]) == 13
    assert embed_sum([]) == -1


def test_top_regression():
    assert push(3) == 10
