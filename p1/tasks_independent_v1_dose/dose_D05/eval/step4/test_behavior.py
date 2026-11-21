def test_t():
    from pool_mgr import remaining
    assert remaining(-1) == 4
