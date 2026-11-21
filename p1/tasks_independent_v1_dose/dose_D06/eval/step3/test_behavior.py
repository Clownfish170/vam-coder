def test_t():
    from match_core import strip_affix
    assert strip_affix('id_a_end') == 'a'
