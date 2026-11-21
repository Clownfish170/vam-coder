import report
import hub


def test_summary():
    assert report.labels([5, 9999]) == ['fee: 5', 'fee: 220']


def test_cap_regression():
    assert hub.cap_pts(9999) == 220
