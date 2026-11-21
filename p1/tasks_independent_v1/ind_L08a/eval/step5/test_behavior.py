import pytest
import plug
import shell


def _seed():
    plug.HANDLERS.clear()
    plug.ALIASES.clear()
    plug.register("greet", lambda: "hi")


def test_alias_dispatch():
    _seed()
    plug.alias("hi", "greet")
    assert plug.dispatch("hi") == "hi"


def test_alias_target_missing():
    _seed()
    with pytest.raises(KeyError):
        plug.alias("x", "ghost")


def test_shell_regression():
    _seed()
    assert shell.run("greet") == "hi"
