import report
import hub


def test_summary():
    assert report.summary([5, 9999]) == ['fee: 5', 'fee: 250']


def test_cap_regression():
    assert hub.cap_fee(9999) == 250
