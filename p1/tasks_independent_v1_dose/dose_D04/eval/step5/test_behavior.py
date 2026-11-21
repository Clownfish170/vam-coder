def test_t():
    from fmt_core import join_list
    assert join_list([None, 'a', 'b']) == ('a-b', 2)
