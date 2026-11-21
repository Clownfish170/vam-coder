from impl import build_seq
from api import seq_run


def test_call_default():
    assert seq_run(['a', 'b']) == 'a, b'


def test_call_with_sep():
    assert seq_run(['a', 'b'], ';') == 'a;b'


def test_render_regression():
    assert build_seq(['q'], '|') == 'q'
