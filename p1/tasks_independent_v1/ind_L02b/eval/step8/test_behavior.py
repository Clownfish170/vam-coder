import pytest
import meter


def test_bad_day_format():
    meter.USAGE.clear()
    with pytest.raises(ValueError):
        meter.record("jan-1", 5)
    with pytest.raises(ValueError):
        meter.record("2024/01/01", 5)


def test_good_day_format():
    meter.USAGE.clear()
    meter.record("2024-01-01", 5)
    assert meter.USAGE["2024-01-01"] == 5


def test_peak_regression():
    meter.USAGE.clear()
    meter.record("2024-01-02", 9)
    assert meter.peak() == "2024-01-02"
