import routes


def test_none_becomes_ok():
    routes.bind("/void", lambda p: None)
    assert routes.serve("/void", 1) == "ok"


def test_passthrough():
    routes.bind("/dbl", lambda p: p + p)
    assert routes.serve("/dbl", 4) == 8


def test_alias_regression():
    routes.bind("/hm", lambda p: "y")
    routes.bind_alias("/h2", "/hm")
    assert routes.serve("/h2", None) == "y"
