def test_t():
    from filter_core import keep
    assert keep(15) is True
    assert keep(25) is False
