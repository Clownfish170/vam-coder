from impl import glue
from api import glue_call
from adapter import glue_via


def test_none_filtered():
    assert glue(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert glue(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert glue_call(['a', 'b'], ';') == 'a;b'
    assert glue_via(['x', 'y']) == 'x-y'
    assert glue([]) == ''
