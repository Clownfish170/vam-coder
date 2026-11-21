import ops_log


def test_compact_keeps_two():
    ops_log.OPS.clear()
    for d in (1, 2, 3, 4, 5):
        ops_log.push({"op": "bump", "delta": d})
    assert ops_log.compact() == 5
    assert ops_log.length() == 2
    assert ops_log.OPS == [
        {"op": "bump", "delta": 4}, {"op": "bump", "delta": 5}
    ]


def test_compact_short_log():
    ops_log.OPS.clear()
    ops_log.push({"op": "bump", "delta": 1})
    ops_log.compact()
    assert ops_log.length() == 1


def test_compact_empty_regression():
    ops_log.OPS.clear()
    assert ops_log.compact() == 0
