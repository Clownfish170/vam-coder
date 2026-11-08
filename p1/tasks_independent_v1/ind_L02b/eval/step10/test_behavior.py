import prices
import meter
import billing


def test_quota_updated():
    assert prices.FREE_QUOTA == 30
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    assert meter.day_charge("2024-01-01") == 0
    assert meter.days_over() == []


def test_full_chain():
    meter.USAGE.clear()
    meter.record("2024-01-01", 40)
    meter.record("2024-01-02", 10)
    assert meter.total_units() == 50
    assert meter.peak() == "2024-01-01"
    assert meter.days_over() == ["2024-01-01"]
    assert meter.day_charge("2024-01-01") == 80
    assert billing.total_charge() == 80
    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=80"
