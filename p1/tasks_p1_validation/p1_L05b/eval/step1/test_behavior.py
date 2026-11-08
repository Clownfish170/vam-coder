from leaf import fold


def test_shape():
    assert fold(-2) == -1
    assert fold(3) == 9
    assert fold(0) == 0
