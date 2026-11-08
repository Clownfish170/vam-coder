import ratio


def test_basic():
    assert ratio.simplify(4, 6) == (2, 3)


def test_sign():
    assert ratio.simplify(-4, 6) == (-2, 3)


def test_zero_zero():
    assert ratio.simplify(0, 0) == (0, 1)


def test_already_reduced():
    assert ratio.simplify(3, 5) == (3, 5)
