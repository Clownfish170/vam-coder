import pytest
import plug
import hooks
import shell


def _seed():
    plug.HANDLERS.clear()
    plug.ALIASES.clear()
    hooks.AFTER.clear()


def test_strict_default_false():
    _seed()
    assert plug.STRICT is False
    assert plug.dispatch("missing") is None


def test_strict_override():
    _seed()
    plug.STRICT = True
    with pytest.raises(KeyError):
        plug.dispatch("missing")


def test_full_chain():
    _seed()
    plug.STRICT = False
    plug.register("greet", lambda n: f"hi {n}")
    plug.alias("hi", "greet")
    seen = []
    hooks.on_after(lambda name, result: seen.append((name, result)))
    assert plug.dispatch("hi", "bob") == "hi bob"
    assert seen == [("greet", "hi bob")]
    assert plug.names() == ["greet"]
    assert shell.run("ghost") is None
