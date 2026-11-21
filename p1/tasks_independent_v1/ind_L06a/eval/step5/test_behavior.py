import gateway
import codec


def test_route_v1():
    assert gateway.route("hi|there") == "hi"


def test_route_v2():
    assert gateway.route("v2|ping|body|tag") == "ping"


def test_addr_regression():
    assert gateway.addr() == "gw-1"


def test_decode_any_regression():
    assert codec.decode_any("k|v") == ("k", "v")
