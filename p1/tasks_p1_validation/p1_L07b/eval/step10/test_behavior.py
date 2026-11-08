from mid import amp
from top import serve_s, serve_many
from leaf import mean_sum


def test_top_boost_applied():
    assert serve_s(3) == 12


def test_agg_follows_top():
    assert serve_many([3]) == [12]


def test_full_chain_regression():
    assert amp(3, 2) == 12
    assert mean_sum([2, 3]) == 13
    assert mean_sum([2, -1]) == -1
