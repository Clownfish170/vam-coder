from mid import align
from top import flush
from leaf import pad_sum


def test_synced_signature():
    assert align(3, 2) == 12
    assert flush(3) == 10


def test_leaf_regression():
    assert pad_sum([2, 3]) == 13
