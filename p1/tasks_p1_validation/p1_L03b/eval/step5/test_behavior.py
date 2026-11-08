from mid import bias
from top import push
from leaf import embed_sum


def test_synced_signature():
    assert bias(3, 2) == 12
    assert push(3) == 10


def test_leaf_regression():
    assert embed_sum([2, 3]) == 13
