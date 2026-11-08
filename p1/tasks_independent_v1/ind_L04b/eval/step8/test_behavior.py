import ops_log


def test_compact():
    ops_log.OPS.clear()
    for d in (1, 2, 3):
        ops_log.push({"op": "bump", "delta": d})
    assert ops_log.compact() == 3
    assert ops_log.length() == 0


def test_compact_empty():
    ops_log.OPS.clear()
    assert ops_log.compact() == 0


def test_last_op_regression():
    ops_log.OPS.clear()
    ops_log.push({"op": "bump", "delta": 7})
    assert ops_log.last_op() == {"op": "bump", "delta": 7}
