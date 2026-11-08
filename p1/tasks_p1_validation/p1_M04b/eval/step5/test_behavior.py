from impl import write_row
from api import send
from adapter import write_via


def test_none_filtered():
    assert write_row(['a', None, 'b']) == 'a, b'


def test_explicit_sep_filtered():
    assert write_row(['a', None, 'b'], ';') == 'a;b'


def test_chain_regressions():
    assert send(['a', 'b'], ';') == 'a;b'
    assert write_via(['x', 'y']) == 'x-y'
    assert write_row([]) == ''
