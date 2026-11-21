import pytest
import meter


def test_reject_negative():
    meter.USAGE.clear()
    with pytest.raises(ValueError):
        meter.record("2024-01-01", -1)


def test_record_ok():
    meter.USAGE.clear()
    meter.record("2024-01-01", 4)
    assert meter.total_units() == 4
