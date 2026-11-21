from impl import print_stream


def test_separator():
    assert print_stream(['a', 'b']) == 'a, b'
    assert print_stream(['x']) == 'x'
