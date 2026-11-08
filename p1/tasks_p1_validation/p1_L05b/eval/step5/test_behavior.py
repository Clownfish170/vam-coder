from mid import step
from top import drive
from leaf import fold_sum


def test_synced_signature():
    assert step(3, 2) == 12
    assert drive(3) == 10


def test_leaf_regression():
    assert fold_sum([2, 3]) == 13
