import pytest
import plug
import hooks


def _seed():
    plug.HANDLERS.clear()
    plug.ALIASES.clear()
    hooks.AFTER.clear()
    plug.register("real", lambda: "ok")


def test_alias_chain():
    _seed()
    plug.alias("a", "real")
    plug.alias("b", "a")
    assert plug.dispatch("b") == "ok"


def test_alias_loop():
    _seed()
    plug.register("r", lambda: 1)
    plug.alias("p", "r")
    plug.alias("q", "p")
    plug.alias("p", "q")
    with pytest.raises(ValueError):
        plug.dispatch("p")


def test_single_alias_regression():
    _seed()
    plug.alias("s", "real")
    assert plug.dispatch("s") == "ok"
