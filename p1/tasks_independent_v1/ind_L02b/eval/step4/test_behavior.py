import meter


def test_days_over():
    meter.USAGE.clear()
    meter.record("2024-01-03", 30)
    meter.record("2024-01-01", 21)
    meter.record("2024-01-02", 5)
    assert meter.days_over() == ["2024-01-01", "2024-01-03"]


def test_days_over_empty():
    meter.USAGE.clear()
    meter.record("2024-01-01", 1)
    assert meter.days_over() == []


def test_charge_regression():
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    assert meter.day_charge("2024-01-01") == 25
