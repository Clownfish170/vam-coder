def test_t():
    from router import resolve
    assert resolve('x') == '/home'
