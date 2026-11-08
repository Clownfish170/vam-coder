import meter


def test_total():
    meter.USAGE.clear()
    meter.record("2024-01-01", 10)
    meter.record("2024-01-02", 5)
    assert meter.total_units() == 15


def test_total_empty():
    meter.USAGE.clear()
    assert meter.total_units() == 0


def test_record_regression():
    meter.USAGE.clear()
    meter.record("2024-01-01", 3)
    assert meter.USAGE["2024-01-01"] == 3
