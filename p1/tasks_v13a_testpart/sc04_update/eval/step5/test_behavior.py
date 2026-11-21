def test():
    from biz import gross
    assert abs(gross(10) - 25.0) < 1e-9
