from impl import render


def test_default_sep():
    assert render(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert render(['a', 'b'], ';') == 'a;b'
