from impl import join_items


def test_default_sep():
    assert join_items(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert join_items(['a', 'b'], ';') == 'a;b'
