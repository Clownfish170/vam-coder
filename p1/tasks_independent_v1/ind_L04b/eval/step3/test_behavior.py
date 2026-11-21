import counter
import ops_log


def test_bump_records():
    counter.VALUE = 0
    ops_log.OPS.clear()
    counter.bump(4)
    assert counter.VALUE == 4
    assert ops_log.OPS == [{"op": "bump", "delta": 4}]


def test_bump_twice_records():
    counter.VALUE = 0
    ops_log.OPS.clear()
    counter.bump(1)
    counter.bump(2)
    assert ops_log.length() == 2
    assert counter.VALUE == 3


def test_get_regression():
    counter.VALUE = 7
    assert counter.get() == 7
