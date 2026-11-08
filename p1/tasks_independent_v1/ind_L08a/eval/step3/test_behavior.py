import pytest
import plug


def test_duplicate_rejected():
    plug.HANDLERS.clear()
    plug.register("a", lambda: 1)
    with pytest.raises(ValueError):
        plug.register("a", lambda: 2)
    assert plug.dispatch("a") == 1


def test_new_name_ok():
    plug.HANDLERS.clear()
    plug.register("a", lambda: 1)
    plug.register("b", lambda: 2)
    assert plug.dispatch("b") == 2


def test_dispatch_regression():
    plug.HANDLERS.clear()
    plug.register("double", lambda x: x * 2)
    assert plug.dispatch("double", 5) == 10
