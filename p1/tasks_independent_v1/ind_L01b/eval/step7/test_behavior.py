import desk


def test_levels():
    desk.BUCKETS.clear()
    desk.admit("a", 2)
    desk.admit("b", 7)
    desk.admit("c", 2)
    assert desk.levels() == [7, 2]


def test_levels_skips_empty():
    desk.BUCKETS.clear()
    desk.admit("a", 4)
    desk.next_job()
    assert desk.levels() == []


def test_drain_regression():
    desk.BUCKETS.clear()
    desk.admit("a", 3)
    desk.admit("b", 3)
    assert desk.drain(3, 5) == ["a", "b"]
