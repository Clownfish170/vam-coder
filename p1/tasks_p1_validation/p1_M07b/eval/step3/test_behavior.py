from impl import glue
from api import glue_call


def test_call_default():
    assert glue_call(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert glue_call(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert glue(['q'], '|') == 'q'
