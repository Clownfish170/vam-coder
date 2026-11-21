def test():
    from biz import gross
    assert abs(gross(10) - 12.5) < 1e-9
