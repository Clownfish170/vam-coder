def test():
    from bill import total
    assert abs(total(4) - 1.0) < 1e-9
