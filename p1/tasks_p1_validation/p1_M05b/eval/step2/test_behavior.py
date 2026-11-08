from impl import print_stream


def test_default_sep():
    assert print_stream(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert print_stream(['a', 'b'], ';') == 'a;b'
