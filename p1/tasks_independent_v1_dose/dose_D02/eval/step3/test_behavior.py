def test_t():
    from router import has_alias
    assert has_alias('h') is True
    assert has_alias('z') is False
