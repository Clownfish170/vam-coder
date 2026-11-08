import app
import registry


def test_bye_registered():
    assert registry.dispatch("bye", "now") == "bye now"


def test_hello_regression():
    assert registry.dispatch("hello", "there") == "hi there"


def test_none_ok_regression():
    registry.register("s2", lambda a: None)
    assert registry.dispatch("s2", 0) == "ok"
