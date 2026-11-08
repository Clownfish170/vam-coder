import api, app


def test_request():
    assert api.Client().request('u') == 'GET:u'


def test_fetch_gone():
    assert not hasattr(api.Client, 'fetch')


def test_go():
    assert app.go() == 'GET:u'
