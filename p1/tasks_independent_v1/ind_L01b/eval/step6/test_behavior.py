import desk
import pytest


def test_default_level():
    desk.BUCKETS.clear()
    desk.admit("auto")
    assert desk.count(1) == 1
    assert desk.next_job() == "auto"


def test_explicit_level_regression():
    desk.BUCKETS.clear()
    desk.admit("x", 6)
    assert desk.count(6) == 1


def test_bounds_regression():
    desk.BUCKETS.clear()
    with pytest.raises(ValueError):
        desk.admit("bad", 99)
