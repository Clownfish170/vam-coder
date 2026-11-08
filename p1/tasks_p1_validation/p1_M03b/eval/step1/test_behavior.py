from impl import join_items


def test_separator():
    assert join_items(['a', 'b']) == 'a, b'
    assert join_items(['x']) == 'x'
