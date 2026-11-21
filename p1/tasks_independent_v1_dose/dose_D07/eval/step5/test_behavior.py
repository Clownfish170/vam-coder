def test_t():
    from score_core import total
    assert total([1, 2]) == 9
    assert total([]) == 0
