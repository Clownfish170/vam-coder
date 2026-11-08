from mid import gate
from top import dispatch, dispatch_all
from leaf import render_sum


def test_top_boost_applied():
    assert dispatch(3) == 11


def test_agg_follows_top():
    assert dispatch_all([3]) == [11]


def test_full_chain_regression():
    assert gate(3, 2) == 12
    assert render_sum([2, 3]) == 13
    assert render_sum([2, -1]) == -1
