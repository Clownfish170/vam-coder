import hub
import policy
import report


def test_cap():
    assert hub.bound(9999) == 200
    assert hub.bound(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 200
    assert policy.within(1) is True


def test_report_regression():
    assert report.emit(3) == 'fee: 6'
