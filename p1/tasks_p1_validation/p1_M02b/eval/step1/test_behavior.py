from impl import emit


def test_separator():
    assert emit(['a', 'b']) == 'a, b'
    assert emit(['x']) == 'x'
