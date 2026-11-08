import counter
import report


def test_status():
    counter.VALUE = 12
    assert report.status() == "value=12"


def test_status_zero():
    counter.VALUE = 0
    assert report.status() == "value=0"


def test_banner_regression():
    assert report.banner() == "counter-report"
