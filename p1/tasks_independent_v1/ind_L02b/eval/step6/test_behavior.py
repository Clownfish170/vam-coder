import prices
import meter
import billing


def test_price_updated():
    assert prices.UNIT_PRICE == 8
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    assert meter.day_charge("2024-01-01") == 40
    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=40"


def test_under_quota_regression():
    meter.USAGE.clear()
    meter.record("2024-01-01", 10)
    assert meter.day_charge("2024-01-01") == 0
