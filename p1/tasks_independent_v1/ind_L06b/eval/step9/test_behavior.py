import bridge


def test_negotiate_min():
    assert bridge.negotiate([1, 2]) == 1


def test_negotiate_subset():
    assert bridge.negotiate([2]) == 2


def test_negotiate_none():
    assert bridge.negotiate([3, 4]) is None


def test_dispatch_regression():
    assert bridge.dispatch("#2 ping:a=1") == "ping"
