from impl import build_seq
from api import seq_run
from adapter import seq_via


def test_via_dash():
    assert seq_via(['x', 'y']) == 'x-y'


def test_call_regression():
    assert seq_run(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert build_seq(['a', 'b']) == 'a, b'
