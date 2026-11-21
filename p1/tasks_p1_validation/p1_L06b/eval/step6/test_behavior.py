from top import relay
from cache import load_cell_serve
from mid import shift


def test_cache_consumer():
    assert load_cell_serve(3) == 11


def test_mid_regression():
    assert shift(3, 0) == 10
