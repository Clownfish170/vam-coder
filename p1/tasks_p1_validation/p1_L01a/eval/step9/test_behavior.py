import hub
import report


def test_cap_negative():
    assert hub.cap_fee(-3) == 0
    assert hub.cap_fee(9999) == 250


def test_summary_regression():
    assert report.summary([5, 9999]) == ['fee: 5', 'fee: 250']
