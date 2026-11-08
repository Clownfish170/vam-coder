import meter


def test_peak():
    meter.USAGE.clear()
    meter.record("2024-01-02", 12)
    meter.record("2024-01-01", 30)
    meter.record("2024-01-03", 30)
    assert meter.peak() == "2024-01-01"


def test_peak_empty():
    meter.USAGE.clear()
    assert meter.peak() is None


def test_charge_regression():
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    assert meter.day_charge("2024-01-01") == 40
