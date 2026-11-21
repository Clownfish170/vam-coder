from leaf import embed


def test_shape():
    assert embed(-2) == -1
    assert embed(3) == 9
    assert embed(0) == 0
