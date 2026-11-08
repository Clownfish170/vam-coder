from leaf import meanish


def test_shape():
    assert meanish(-2) == -1
    assert meanish(3) == 9
    assert meanish(0) == 0
