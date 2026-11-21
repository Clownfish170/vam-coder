from impl import render


def test_separator():
    assert render(['a', 'b']) == 'a, b'
    assert render(['x']) == 'x'
