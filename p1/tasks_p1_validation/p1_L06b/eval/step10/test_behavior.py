from mid import shift
from top import relay, relay_all
from leaf import grow_sum


def test_top_boost_applied():
    assert relay(3) == 11


def test_agg_follows_top():
    assert relay_all([3]) == [11]


def test_full_chain_regression():
    assert shift(3, 2) == 12
    assert grow_sum([2, 3]) == 13
    assert grow_sum([2, -1]) == -1
