from mid import shift
from top import relay
from leaf import grow_sum


def test_synced_signature():
    assert shift(3, 2) == 12
    assert relay(3) == 10


def test_leaf_regression():
    assert grow_sum([2, 3]) == 13
