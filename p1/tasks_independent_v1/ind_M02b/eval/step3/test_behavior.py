import totals


def test_count():
    assert totals.count_items() == 2


def test_sum_regression():
    assert totals.sum_prices() == 7
