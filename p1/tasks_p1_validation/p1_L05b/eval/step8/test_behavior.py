from top import drive, drive_all
from cache import arm_serve


def test_agg():
    assert drive_all([3, 4]) == [10, 17]


def test_cache_regression():
    assert arm_serve(3) == 12
