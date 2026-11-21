import ops_log


def test_length_empty():
    ops_log.OPS.clear()
    assert ops_log.length() == 0


def test_length_after_push():
    ops_log.OPS.clear()
    ops_log.push({"op": "bump", "delta": 1})
    ops_log.push({"op": "bump", "delta": 2})
    assert ops_log.length() == 2


def test_push_regression():
    ops_log.OPS.clear()
    ops_log.push({"op": "bump", "delta": 1})
    assert ops_log.OPS == [{"op": "bump", "delta": 1}]
