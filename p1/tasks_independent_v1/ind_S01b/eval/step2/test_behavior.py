import tax


def test_zero_identity():
    assert tax.apply_discount(80, 0) == 80


def test_clamp_over():
    assert tax.apply_discount(100, 150) == 0


def test_negative_clamp():
    assert tax.apply_discount(100, -5) == 100


def test_regression():
    assert tax.apply_discount(100, 10) == 90.0
