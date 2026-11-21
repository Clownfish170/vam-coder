def test():
    from bill import fee
    assert abs(fee(4) - 4.0) < 1e-9
