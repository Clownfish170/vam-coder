from leaf import grow


def test_shape():
    assert grow(-2) == -1
    assert grow(3) == 9
    assert grow(0) == 0
