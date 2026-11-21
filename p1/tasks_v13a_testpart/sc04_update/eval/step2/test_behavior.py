def test():
    from taxrate import RATE
    assert abs(RATE - 0.25) < 1e-9
