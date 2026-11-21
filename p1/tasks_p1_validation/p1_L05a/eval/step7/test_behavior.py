import hub
import policy
import report


def test_cap():
    assert hub.cap_pts(9999) == 220
    assert hub.cap_pts(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 220
    assert policy.cap_ok(1) is True


def test_report_regression():
    assert report.label_for(3) == 'fee: 18'
