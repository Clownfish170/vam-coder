import shipping


def test_clamp_high():
    assert shipping.surcharge(100, 150) == 100.0


def test_clamp_low():
    assert shipping.surcharge(100, -5) == 0.0


def test_normal_regression():
    assert shipping.surcharge(200, 15) == 30.0
