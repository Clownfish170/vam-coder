from leaf import pad


def test_shape():
    assert pad(-2) == -1
    assert pad(3) == 9
    assert pad(0) == 0
