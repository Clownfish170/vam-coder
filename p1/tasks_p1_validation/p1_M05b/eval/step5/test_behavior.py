from impl import print_stream
from api import push
from adapter import print_via


def test_none_filtered():
    assert print_stream(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert print_stream(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert push(['a', 'b'], ';') == 'a;b'
    assert print_via(['x', 'y']) == 'x-y'
    assert print_stream([]) == ''
