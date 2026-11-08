from impl import join_cells
from api import open_cells
from adapter import cells_via


def test_none_filtered():
    assert join_cells(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert join_cells(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert open_cells(['a', 'b'], ';') == 'a;b'
    assert cells_via(['x', 'y']) == 'x-y'
    assert join_cells([]) == ''
