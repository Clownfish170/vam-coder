from mid import align
from top import flush, flush_all
from leaf import pad_sum


def test_top_boost_applied():
    assert flush(3) == 13


def test_agg_follows_top():
    assert flush_all([3]) == [13]


def test_full_chain_regression():
    assert align(3, 2) == 12
    assert pad_sum([2, 3]) == 13
    assert pad_sum([2, -1]) == -1
