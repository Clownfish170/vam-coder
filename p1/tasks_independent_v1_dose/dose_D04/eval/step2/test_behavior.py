def test_t():
    from fmt_core import join3
    assert join3('a', None, 'c') == 'a--c'
