from impl import print_stream
from api import push


def test_call_default():
    assert push(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert push(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert print_stream(['q'], '|') == 'q'
