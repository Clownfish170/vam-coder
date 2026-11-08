import bridge
import guard


def test_dispatch():
    assert bridge.dispatch("ping:a=1;b=2") == "ping"


def test_dispatch_bad():
    assert bridge.dispatch("cmd:") is None
    assert bridge.dispatch("ping:oops") is None


def test_name_regression():
    assert bridge.name() == "bridge-0"


def test_safe_regression():
    assert guard.is_safe("cmd:") is False
