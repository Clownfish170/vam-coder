import shipping


def test_free_shipment():
    assert shipping.quote(600, 10, 10) == 60.0


def test_below_threshold():
    assert shipping.quote(100, 3, 10) == 18.0


def test_surcharge_regression():
    assert shipping.surcharge(200, 15) == 30.0
