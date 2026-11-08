import counter
import ops_log


def test_redo():
    counter.VALUE = 0
    ops_log.OPS.clear()
    ops_log.UNDONE.clear()
    counter.bump(5)
    counter.undo_last()
    assert counter.redo_last() == 5
    assert counter.VALUE == 5
    assert ops_log.length() == 1
    assert ops_log.UNDONE == []


def test_redo_empty():
    counter.VALUE = 0
    ops_log.OPS.clear()
    ops_log.UNDONE.clear()
    assert counter.redo_last() is None


def test_undo_regression():
    counter.VALUE = 0
    ops_log.OPS.clear()
    ops_log.UNDONE.clear()
    counter.bump(4)
    assert counter.undo_last() == {"op": "bump", "delta": 4}
    assert counter.VALUE == 0
