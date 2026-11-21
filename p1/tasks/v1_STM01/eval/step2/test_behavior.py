import pricing, discount


def test_price():
    assert pricing.price(3) == 36


def test_fast():
    assert discount.fast_price(3) == 36
    assert discount.fast_price(10) == 120


def test_total():
    assert discount.total(3) == 36
