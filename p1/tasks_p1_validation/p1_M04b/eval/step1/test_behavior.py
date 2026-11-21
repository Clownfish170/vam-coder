from impl import write_row


def test_separator():
    assert write_row(['a', 'b']) == 'a, b'
    assert write_row(['x']) == 'x'
