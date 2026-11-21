import billing
import meter


def test_charge_line():
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=25"


def test_header_regression():
    assert billing.header() == "bill"


def test_days_over_regression():
    meter.USAGE.clear()
    meter.record("2024-01-05", 40)
    assert meter.days_over() == ["2024-01-05"]
