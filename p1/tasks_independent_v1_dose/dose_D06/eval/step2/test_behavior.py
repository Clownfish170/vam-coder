def test_t():
    from match_core import match
    assert match('id_a_end') is True
    assert match('id_a') is False
