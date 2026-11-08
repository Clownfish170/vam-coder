import shipping


def test_surcharge_pct():
    assert shipping.surcharge(200, 15) == 30.0


def test_surcharge_zero():
    assert shipping.surcharge(200, 0) == 0.0


def test_weight_fee_regression():
    assert shipping.weight_fee(3) == 8
