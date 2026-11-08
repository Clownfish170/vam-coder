import tax


def test_ten_percent():
    assert tax.apply_discount(100, 10) == 90.0


def test_zero():
    assert tax.apply_discount(80, 0) == 80


def test_half():
    assert tax.apply_discount(200, 50) == 100.0
