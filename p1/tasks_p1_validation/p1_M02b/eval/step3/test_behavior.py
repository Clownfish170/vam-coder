from impl import emit
from api import invoke


def test_call_default():
    assert invoke(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert invoke(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert emit(['q'], '|') == 'q'
