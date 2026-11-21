from impl import glue


def test_separator():
    assert glue(['a', 'b']) == 'a, b'
    assert glue(['x']) == 'x'
