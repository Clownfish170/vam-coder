def test_t():
    from pool_mgr import remaining
    assert remaining(99) == 0
    assert remaining(1) == 3
