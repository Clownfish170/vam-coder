import desk


def test_count():
    desk.BUCKETS.clear()
    desk.admit("a", 2)
    desk.admit("b", 2)
    desk.admit("c", 5)
    assert desk.count(2) == 2
    assert desk.count(5) == 1
    assert desk.count(9) == 0


def test_next_regression():
    desk.BUCKETS.clear()
    desk.admit("low", 1)
    desk.admit("high", 7)
    assert desk.next_job() == "high"
    assert desk.count(7) == 0
