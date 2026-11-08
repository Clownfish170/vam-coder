from impl import render
from api import call
from adapter import render_via


def test_via_dash():
    assert render_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert call(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert render(['a', 'b']) == 'a, b'
