from mid import step
from top import drive, drive_all
from leaf import fold_sum


def test_top_boost_applied():
    assert drive(3) == 12


def test_agg_follows_top():
    assert drive_all([3]) == [12]


def test_full_chain_regression():
    assert step(3, 2) == 12
    assert fold_sum([2, 3]) == 13
    assert fold_sum([2, -1]) == -1
