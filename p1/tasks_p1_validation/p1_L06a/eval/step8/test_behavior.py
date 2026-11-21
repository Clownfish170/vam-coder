import report
import hub


def test_summary():
    assert report.descs([5, 9999]) == ['fee: 5', 'fee: 260']


def test_cap_regression():
    assert hub.cap_rent(9999) == 260
