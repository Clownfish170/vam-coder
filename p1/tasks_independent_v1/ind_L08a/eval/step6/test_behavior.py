import plug
import hooks


def _seed():
    plug.HANDLERS.clear()
    plug.ALIASES.clear()
    hooks.AFTER.clear()
    plug.register("echo", lambda x: x * 3)


def test_hooks_called():
    _seed()
    seen = []
    hooks.on_after(lambda name, result: seen.append((name, result)))
    assert plug.dispatch("echo", 4) == 12
    assert seen == [("echo", 12)]


def test_no_hooks():
    _seed()
    assert plug.dispatch("echo", 1) == 3


def test_alias_regression():
    _seed()
    plug.alias("e", "echo")
    assert plug.dispatch("e", 2) == 6
