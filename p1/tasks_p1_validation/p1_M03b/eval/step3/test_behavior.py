from impl import join_items
from api import run_join


def test_call_default():
    assert run_join(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert run_join(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert join_items(['q'], '|') == 'q'
