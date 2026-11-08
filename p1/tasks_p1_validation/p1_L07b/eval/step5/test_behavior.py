from mid import amp
from top import serve_s
from leaf import mean_sum


def test_synced_signature():
    assert amp(3, 2) == 12
    assert serve_s(3) == 10


def test_leaf_regression():
    assert mean_sum([2, 3]) == 13
