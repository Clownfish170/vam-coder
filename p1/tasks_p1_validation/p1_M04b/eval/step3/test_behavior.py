from impl import write_row
from api import send


def test_call_default():
    assert send(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert send(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert write_row(['q'], '|') == 'q'
