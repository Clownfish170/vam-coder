import hub
import policy
import report


def test_cap():
    assert hub.cap_interest(9999) == 320
    assert hub.cap_interest(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 320
    assert policy.within_i(1) is True


def test_report_regression():
    assert report.line_of(3) == 'fee: 6'
