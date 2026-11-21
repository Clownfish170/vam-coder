import app


def test_is_active():
    assert app.is_active() is True


def test_banner():
    assert app.banner() == 'mode=active'
