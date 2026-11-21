import counter
import ops_log
import report


def test_undo_last():
    counter.VALUE = 0
    ops_log.OPS.clear()
    ops_log.UNDONE.clear()
    counter.bump(5)
    counter.bump(3)
    op = counter.undo_last()
    assert op == {"op": "bump", "delta": 3}
    assert counter.VALUE == 5
    assert ops_log.length() == 1
    assert ops_log.UNDONE == [{"op": "bump", "delta": 3}]


def test_undo_empty():
    counter.VALUE = 0
    ops_log.OPS.clear()
    assert counter.undo_last() is None


def test_status_regression():
    counter.VALUE = 9
    assert report.status() == "value=9"
