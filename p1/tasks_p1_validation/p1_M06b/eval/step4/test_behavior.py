from impl import join_cells
from api import open_cells
from adapter import cells_via


def test_via_dash():
    assert cells_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert open_cells(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert join_cells(['a', 'b']) == 'a, b'
