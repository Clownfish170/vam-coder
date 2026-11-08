from impl import emit
from api import invoke
from adapter import emit_via


def test_via_dash():
    assert emit_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert invoke(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert emit(['a', 'b']) == 'a, b'
