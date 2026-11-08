from impl import glue


def test_default_sep():
    assert glue(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert glue(['a', 'b'], ';') == 'a;b'
