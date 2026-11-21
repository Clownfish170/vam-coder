def test_t():
    from pool_mgr import acquire
    assert acquire() == 4
