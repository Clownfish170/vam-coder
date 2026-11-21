def test_t():
    from router import resolve
    assert resolve('h') == '/alias_home'
    assert resolve('z') == '/home'
