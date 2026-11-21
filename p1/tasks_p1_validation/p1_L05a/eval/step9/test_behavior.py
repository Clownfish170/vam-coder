import hub
import report


def test_cap_negative():
    assert hub.cap_pts(-3) == 0
    assert hub.cap_pts(9999) == 220


def test_summary_regression():
    assert report.labels([5, 9999]) == ['fee: 5', 'fee: 220']
