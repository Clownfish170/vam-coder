from mid import tune
from top import handle, handle_all
from leaf import sum_all


def test_top_boost_applied():
    assert handle(3) == 12


def test_agg_follows_top():
    assert handle_all([3]) == [12]


def test_full_chain_regression():
    assert tune(3, 2) == 12
    assert sum_all([2, 3]) == 13
    assert sum_all([2, -1]) == -1
