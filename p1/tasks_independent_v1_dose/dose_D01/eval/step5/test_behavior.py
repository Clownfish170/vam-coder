def test_t():
    from bill_core import charge
    assert charge(-1) == 0
    assert charge(2) == 12
