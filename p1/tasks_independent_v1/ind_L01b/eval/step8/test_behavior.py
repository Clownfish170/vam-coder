import desk


def test_clamp_high():
    desk.BUCKETS.clear()
    desk.admit("x", 99)
    assert desk.count(9) == 1
    assert desk.next_job() == "x"


def test_clamp_low():
    desk.BUCKETS.clear()
    desk.admit("y", -5)
    assert desk.count(0) == 1


def test_levels_regression():
    desk.BUCKETS.clear()
    desk.admit("a", 2)
    desk.admit("b", 7)
    assert desk.levels() == [7, 2]
