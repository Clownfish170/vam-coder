from impl import render
from api import call
from adapter import render_via


def test_none_filtered():
    assert render(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert render(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert call(['a', 'b'], ';') == 'a;b'
    assert render_via(['x', 'y']) == 'x-y'
    assert render([]) == ''
