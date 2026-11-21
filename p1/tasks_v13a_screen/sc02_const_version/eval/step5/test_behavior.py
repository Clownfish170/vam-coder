def test_fee():
    from app import fee
    assert abs(fee(1) - 1.2) < 1e-9
