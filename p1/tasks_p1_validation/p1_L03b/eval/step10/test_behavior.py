from mid import bias
from top import push, push_all
from leaf import embed_sum


def test_top_boost_applied():
    assert push(3) == 11


def test_agg_follows_top():
    assert push_all([3]) == [11]


def test_full_chain_regression():
    assert bias(3, 2) == 12
    assert embed_sum([2, 3]) == 13
    assert embed_sum([2, -1]) == -1
