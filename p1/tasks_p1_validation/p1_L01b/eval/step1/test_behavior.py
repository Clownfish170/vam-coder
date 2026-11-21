from leaf import shape


def test_shape():
    assert shape(-2) == -1
    assert shape(3) == 9
    assert shape(0) == 0
