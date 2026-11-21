def test_price():
    from app import price
    assert abs(price(10) - 10 * 1.2 * 2) < 1e-9
