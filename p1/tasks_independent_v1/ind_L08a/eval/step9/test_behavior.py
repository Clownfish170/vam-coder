import pytest
import plug
import hooks


def _seed():
    plug.HANDLERS.clear()
    plug.ALIASES.clear()
    hooks.AFTER.clear()


def test_strict_true():
    _seed()
    assert plug.STRICT is True
    with pytest.raises(KeyError):
        plug.dispatch("missing")


def test_strict_false():
    _seed()
    plug.STRICT = False
    assert plug.dispatch("missing") is None


def test_registered_still_works():
    _seed()
    plug.register("r", lambda: 5)
    assert plug.dispatch("r") == 5
