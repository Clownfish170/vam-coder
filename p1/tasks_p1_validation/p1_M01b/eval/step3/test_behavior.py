from impl import render
from api import call


def test_call_default():
    assert call(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert call(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert render(['q'], '|') == 'q'
