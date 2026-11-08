import meter


def test_charge_over():
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    assert meter.day_charge("2024-01-01") == 25


def test_charge_under():
    meter.USAGE.clear()
    meter.record("2024-01-01", 10)
    assert meter.day_charge("2024-01-01") == 0


def test_charge_missing_day():
    meter.USAGE.clear()
    assert meter.day_charge("2024-01-09") == 0


def test_total_regression():
    meter.USAGE.clear()
    meter.record("2024-01-01", 6)
    assert meter.total_units() == 6
