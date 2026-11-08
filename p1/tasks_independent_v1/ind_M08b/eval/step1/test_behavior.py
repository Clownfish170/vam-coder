import pytest
import routes


def test_unknown_route():
    with pytest.raises(routes.UnknownRoute):
        routes.serve("/zz", "")


def test_known_route():
    routes.bind("/x", lambda p: p)
    assert routes.serve("/x", 9) == 9


def test_paths_regression():
    assert "/x" in routes.paths()
