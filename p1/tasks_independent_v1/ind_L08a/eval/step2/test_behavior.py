import pytest
import plug


def test_dispatch():
    plug.HANDLERS.clear()
    plug.register("double", lambda x: x * 2)
    assert plug.dispatch("double", 5) == 10


def test_dispatch_missing():
    plug.HANDLERS.clear()
    with pytest.raises(KeyError):
        plug.dispatch("nope")


def test_names_regression():
    plug.HANDLERS.clear()
    plug.register("x", lambda: 1)
    assert plug.names() == ["x"]
