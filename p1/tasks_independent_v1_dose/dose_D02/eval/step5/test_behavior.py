def test_t():
    from router import has_alias
    assert has_alias('h') is False
    assert has_alias('') is False
