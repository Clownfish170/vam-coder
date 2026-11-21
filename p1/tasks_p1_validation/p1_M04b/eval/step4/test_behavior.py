from impl import write_row
from api import send
from adapter import write_via


def test_via_dash():
    assert write_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert send(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert write_row(['a', 'b']) == 'a, b'
