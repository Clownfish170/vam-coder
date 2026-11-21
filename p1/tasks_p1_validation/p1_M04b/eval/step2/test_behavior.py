from impl import write_row


def test_default_sep():
    assert write_row(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert write_row(['a', 'b'], ';') == 'a;b'
