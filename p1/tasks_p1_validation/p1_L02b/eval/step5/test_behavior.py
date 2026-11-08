from mid import tune
from top import handle
from leaf import sum_all


def test_synced_signature():
    assert tune(3, 2) == 12
    assert handle(3) == 10


def test_leaf_regression():
    assert sum_all([2, 3]) == 13
