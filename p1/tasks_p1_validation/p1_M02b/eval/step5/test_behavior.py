from impl import emit
from api import invoke
from adapter import emit_via


def test_none_filtered():
    assert emit(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert emit(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert invoke(['a', 'b'], ';') == 'a;b'
    assert emit_via(['x', 'y']) == 'x-y'
    assert emit([]) == ''
