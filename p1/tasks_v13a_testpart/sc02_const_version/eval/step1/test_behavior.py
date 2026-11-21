def test_fee():
    from app import fee
    assert abs(fee(1) - 2.0) < 1e-9
