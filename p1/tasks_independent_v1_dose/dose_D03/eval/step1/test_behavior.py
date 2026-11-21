def test_t():
    from filter_core import keep
    assert keep(10) is True
    assert keep(9) is False
