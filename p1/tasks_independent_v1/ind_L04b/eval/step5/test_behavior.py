import ops_log


def test_last_op():
    ops_log.OPS.clear()
    ops_log.push({"op": "bump", "delta": 3})
    assert ops_log.last_op() == {"op": "bump", "delta": 3}


def test_last_op_empty():
    ops_log.OPS.clear()
    assert ops_log.last_op() is None


def test_length_regression():
    ops_log.OPS.clear()
    ops_log.push({"op": "bump", "delta": 1})
    assert ops_log.length() == 1
