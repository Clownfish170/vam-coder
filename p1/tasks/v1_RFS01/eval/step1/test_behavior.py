import app


def test_banner():
    assert app.banner() == 'mode=active'
