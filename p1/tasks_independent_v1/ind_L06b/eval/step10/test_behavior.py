import bridge
import wire
import guard


def test_negotiate_max():
    assert bridge.negotiate([1, 2]) == 2


def test_negotiate_subset_regression():
    assert bridge.negotiate([2]) == 2
    assert bridge.negotiate([1]) == 1


def test_negotiate_none_regression():
    assert bridge.negotiate([5]) is None


def test_full_chain():
    assert wire.unpack_any(wire.pack2(9, "go", "x=1")) == (9, "go", "x=1")
    assert guard.is_safe("go:x=1") is True
    assert bridge.dispatch("#9 go:x=1") == "go"
    assert bridge.negotiate([1, 2, 3]) == 2
