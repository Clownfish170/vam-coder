def test():
    from bill import total
    assert abs(total(8) - 4.0) < 1e-9
    assert abs(total(4) - 2.0) < 1e-9
