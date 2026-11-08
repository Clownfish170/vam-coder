from impl import join_items
from api import run_join
from adapter import join_via


def test_via_dash():
    assert join_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert run_join(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert join_items(['a', 'b']) == 'a, b'
