import routes


def test_registration_order():
    routes.ROUTES.clear()
    routes.ORDER.clear()
    routes.bind("/zeta", lambda p: 1)
    routes.bind("/alpha", lambda p: 2)
    assert routes.paths() == ["/zeta", "/alpha"]


def test_serve_still_works():
    assert routes.serve("/zeta", "") == 1


def test_unknown_regression():
    import pytest
    with pytest.raises(routes.UnknownRoute):
        routes.serve("/ghost", "")
