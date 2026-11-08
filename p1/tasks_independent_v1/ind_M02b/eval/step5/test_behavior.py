import totals
import catalog


def test_sum_cents():
    assert totals.sum_prices() == 700


def test_count_regression():
    assert totals.count_items() == 2


def test_catalog_regression():
    assert catalog.load()["a1"]["cost_cents"] == 200
