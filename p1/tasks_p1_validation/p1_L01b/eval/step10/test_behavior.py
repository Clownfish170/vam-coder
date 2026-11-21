from mid import adjust
from top import serve, serve_all
from leaf import total


def test_top_boost_applied():
    assert serve(3) == 11


def test_agg_follows_top():
    assert serve_all([3]) == [11]


def test_full_chain_regression():
    assert adjust(3, 2) == 12
    assert total([2, 3]) == 13
    assert total([2, -1]) == -1
