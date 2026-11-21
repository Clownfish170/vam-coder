def test_apply_neg():
    from engine import apply
    assert apply(-1) == 0
    assert apply(4) == 12
