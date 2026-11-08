from mid import adjust
from top import serve
from leaf import total


def test_synced_signature():
    assert adjust(3, 2) == 12
    assert serve(3) == 10


def test_leaf_regression():
    assert total([2, 3]) == 13
