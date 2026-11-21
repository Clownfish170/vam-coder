import hooks
import plug


def test_clear():
    hooks.AFTER.clear()
    hooks.on_after(lambda n, r: None)
    hooks.on_after(lambda n, r: None)
    assert hooks.clear() == 2
    assert hooks.AFTER == []


def test_clear_empty():
    hooks.AFTER.clear()
    assert hooks.clear() == 0


def test_hook_dispatch_regression():
    plug.HANDLERS.clear()
    plug.ALIASES.clear()
    hooks.AFTER.clear()
    plug.register("echo", lambda x: x + 1)
    seen = []
    hooks.on_after(lambda n, r: seen.append(r))
    plug.dispatch("echo", 1)
    assert seen == [2]
