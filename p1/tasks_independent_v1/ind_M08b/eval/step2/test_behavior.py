import routes


def test_bind_alias():
    routes.bind("/home", lambda p: "H")
    routes.bind_alias("/h", "/home")
    assert routes.serve("/h", None) == "H"


def test_unknown_regression():
    import pytest
    with pytest.raises(routes.UnknownRoute):
        routes.serve("/ghost", "")
