def test_t():
    from router import resolve
    assert resolve('z') is None
    assert resolve('h') == '/alias_home'
