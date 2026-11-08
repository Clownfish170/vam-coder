import pytest
import desk


def test_out_of_range():
    desk.BUCKETS.clear()
    with pytest.raises(ValueError):
        desk.admit("x", 10)
    with pytest.raises(ValueError):
        desk.admit("x", -1)


def test_in_range():
    desk.BUCKETS.clear()
    desk.admit("ok", 5)
    assert desk.next_job() == "ok"


def test_high_first_regression():
    desk.BUCKETS.clear()
    desk.admit("low", 1)
    desk.admit("high", 7)
    assert desk.next_job() == "high"
