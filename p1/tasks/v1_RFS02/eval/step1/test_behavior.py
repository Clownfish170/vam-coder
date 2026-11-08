import client, status


def test_code():
    assert status.code() == 404


def test_ok_false():
    assert client.ok() is False
