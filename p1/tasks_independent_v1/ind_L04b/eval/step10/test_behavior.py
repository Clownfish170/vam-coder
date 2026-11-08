import pytest
import counter
import ops_log
import report


def test_bump_zero():
    counter.VALUE = 0
    ops_log.OPS.clear()
    with pytest.raises(ValueError):
        counter.bump(0)


def test_bump_ok():
    counter.VALUE = 0
    ops_log.OPS.clear()
    counter.bump(2)
    assert counter.VALUE == 2
    assert ops_log.length() == 1


def test_full_chain():
    counter.VALUE = 0
    ops_log.OPS.clear()
    ops_log.UNDONE.clear()
    counter.bump(6)
    counter.bump(4)
    assert counter.undo_last() == {"op": "bump", "delta": 4}
    assert counter.redo_last() == 10
    assert ops_log.compact() == 2
    assert ops_log.length() == 2
    assert report.status() == "value=10"
