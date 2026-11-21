import cli


def test_show20():
    assert cli.show('y' * 30) == 'y' * 20
