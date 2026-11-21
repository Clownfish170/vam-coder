import text, cli


def test_wrap():
    assert text.wrap(3, 'abcdef') == 'abc'


def test_show():
    assert cli.show('x' * 30) == 'x' * 10
