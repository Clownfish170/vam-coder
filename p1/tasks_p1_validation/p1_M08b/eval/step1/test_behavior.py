from impl import build_seq


def test_separator():
    assert build_seq(['a', 'b']) == 'a, b'
    assert build_seq(['x']) == 'x'
