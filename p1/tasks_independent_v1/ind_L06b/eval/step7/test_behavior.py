import bridge


def test_dispatch_v2():
    assert bridge.dispatch("#2 ping:a=1") == "ping"


def test_dispatch_v1_regression():
    assert bridge.dispatch("ping:a=1") == "ping"


def test_dispatch_bad_regression():
    assert bridge.dispatch("cmd:") is None
