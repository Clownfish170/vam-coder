import plug


def test_names_order():
    plug.HANDLERS.clear()
    plug.register("b", lambda: 2)
    plug.register("a", lambda: 1)
    assert plug.names() == ["b", "a"]


def test_names_empty():
    plug.HANDLERS.clear()
    assert plug.names() == []


def test_register_regression():
    plug.HANDLERS.clear()
    plug.register("x", lambda: 9)
    assert "x" in plug.HANDLERS
