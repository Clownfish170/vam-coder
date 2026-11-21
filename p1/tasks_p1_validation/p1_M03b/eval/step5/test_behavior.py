from impl import join_items
from api import run_join
from adapter import join_via


def test_none_filtered():
    assert join_items(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert join_items(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert run_join(['a', 'b'], ';') == 'a;b'
    assert join_via(['x', 'y']) == 'x-y'
    assert join_items([]) == ''
