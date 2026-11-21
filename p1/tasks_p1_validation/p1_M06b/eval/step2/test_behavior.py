from impl import join_cells


def test_default_sep():
    assert join_cells(['a', 'b']) == 'a, b'


def test_explicit_sep():
    assert join_cells(['a', 'b'], ';') == 'a;b'
