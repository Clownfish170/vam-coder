import pricing


def test_price():
    assert pricing.price(3) == 36
