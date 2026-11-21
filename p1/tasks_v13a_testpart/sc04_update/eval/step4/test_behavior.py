def test():
    from biz import net
    assert net(0) == -1
    assert abs(net(10) - 8.5) < 1e-9
