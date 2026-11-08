from impl import print_stream
from api import push
from adapter import print_via


def test_via_dash():
    assert print_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert push(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert print_stream(['a', 'b']) == 'a, b'
