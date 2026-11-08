import api


def test_get2():
    assert api.Client().request('u') == 'GET2:u'
