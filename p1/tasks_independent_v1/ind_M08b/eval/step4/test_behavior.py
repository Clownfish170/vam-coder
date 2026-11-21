import web
import routes


def test_health_bound():
    assert routes.serve("/health", None) == "up"


def test_index_regression():
    assert routes.serve("/", "q") == "index:q"


def test_none_ok_regression():
    routes.bind("/void2", lambda p: None)
    assert routes.serve("/void2", 0) == "ok"
