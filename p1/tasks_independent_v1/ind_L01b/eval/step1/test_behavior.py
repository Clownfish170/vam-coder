import desk


def test_high_first():
    desk.BUCKETS.clear()
    desk.admit("low", 1)
    desk.admit("high", 7)
    desk.admit("mid", 4)
    assert desk.next_job() == "high"
    assert desk.next_job() == "mid"
    assert desk.next_job() == "low"


def test_fifo_within_level():
    desk.BUCKETS.clear()
    desk.admit("first", 3)
    desk.admit("second", 3)
    assert desk.next_job() == "first"
    assert desk.next_job() == "second"


def test_empty():
    desk.BUCKETS.clear()
    assert desk.next_job() is None
