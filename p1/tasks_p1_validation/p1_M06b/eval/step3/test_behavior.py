from impl import join_cells
from api import open_cells


def test_call_default():
    assert open_cells(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert open_cells(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert join_cells(['q'], '|') == 'q'
