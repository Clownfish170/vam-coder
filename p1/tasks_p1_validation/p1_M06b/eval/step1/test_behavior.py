from impl import join_cells


def test_separator():
    assert join_cells(['a', 'b']) == 'a, b'
    assert join_cells(['x']) == 'x'
