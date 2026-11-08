from impl import glue
from api import glue_call
from adapter import glue_via


def test_via_dash():
    assert glue_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert glue_call(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert glue(['a', 'b']) == 'a, b'
