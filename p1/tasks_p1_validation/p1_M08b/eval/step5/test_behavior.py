from impl import build_seq
from api import seq_run
from adapter import seq_via


def test_none_filtered():
    assert build_seq(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert build_seq(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert seq_run(['a', 'b'], ';') == 'a;b'
    assert seq_via(['x', 'y']) == 'x-y'
    assert build_seq([]) == ''
