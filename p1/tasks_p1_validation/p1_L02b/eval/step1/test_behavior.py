from leaf import norm


def test_shape():
    assert norm(-2) == -1
    assert norm(3) == 9
    assert norm(0) == 0
