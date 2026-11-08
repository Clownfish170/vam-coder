import hub
import report


def test_cap_negative():
    assert hub.cap_rent(-3) == 0
    assert hub.cap_rent(9999) == 260


def test_summary_regression():
    assert report.descs([5, 9999]) == ['fee: 5', 'fee: 260']
