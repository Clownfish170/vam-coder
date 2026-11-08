import billing
import meter


def test_total_charge():
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    meter.record("2024-01-02", 30)
    assert billing.total_charge() == 120


def test_total_charge_empty():
    meter.USAGE.clear()
    assert billing.total_charge() == 0


def test_charge_line_regression():
    meter.USAGE.clear()
    meter.record("2024-01-01", 25)
    assert billing.charge_line("2024-01-01") == "day=2024-01-01 charge=40"
