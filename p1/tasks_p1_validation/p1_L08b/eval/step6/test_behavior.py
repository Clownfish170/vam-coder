from top import dispatch
from cache import prime_f_serve
from mid import gate


def test_cache_consumer():
    assert prime_f_serve(3) == 11


def test_mid_regression():
    assert gate(3, 0) == 10
