def test():
    from biz import net
    assert abs(net(10) - 10.0) < 1e-9
