import client


def test_is_missing():
    assert client.is_missing() is True
