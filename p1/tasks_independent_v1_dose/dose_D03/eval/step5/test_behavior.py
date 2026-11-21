def test_t():
    from filter_core import keep
    assert keep(10) is False
    assert keep(11) is True
