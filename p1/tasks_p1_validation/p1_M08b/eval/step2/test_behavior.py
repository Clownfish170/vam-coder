from impl import build_seq


def test_default_sep():
    assert build_seq(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert build_seq(['a', 'b'], ';') == 'a;b'
