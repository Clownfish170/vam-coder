from top import drive
from cache import arm_serve
from mid import step


def test_cache_consumer():
    assert arm_serve(3) == 12


def test_mid_regression():
    assert step(3, 0) == 10
