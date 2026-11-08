from mid import gate
from top import dispatch
from leaf import render_sum


def test_synced_signature():
    assert gate(3, 2) == 12
    assert dispatch(3) == 10


def test_leaf_regression():
    assert render_sum([2, 3]) == 13
