from impl import emit


def test_default_sep():
    assert emit(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert emit(['a', 'b'], ';') == 'a;b'
