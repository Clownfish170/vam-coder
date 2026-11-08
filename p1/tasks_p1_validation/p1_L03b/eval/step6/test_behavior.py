from top import push
from cache import prime_t_serve
from mid import bias


def test_cache_consumer():
    assert prime_t_serve(3) == 11


def test_mid_regression():
    assert bias(3, 0) == 10
