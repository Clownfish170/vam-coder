def test_t():
    from match_core import match
    assert match('id_a') is True
    assert match('xx') is False
