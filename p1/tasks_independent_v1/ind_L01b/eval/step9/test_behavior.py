import desk


def test_empty_bucket_removed():
    desk.BUCKETS.clear()
    desk.admit("solo", 5)
    assert desk.next_job() == "solo"
    assert 5 not in desk.BUCKETS


def test_partial_bucket_kept():
    desk.BUCKETS.clear()
    desk.admit("a", 5)
    desk.admit("b", 5)
    assert desk.next_job() == "a"
    assert 5 in desk.BUCKETS
    assert desk.count(5) == 1


def test_clamp_regression():
    desk.BUCKETS.clear()
    desk.admit("x", 99)
    assert desk.count(9) == 1
