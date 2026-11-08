import hub
import policy
import report


def test_cap():
    assert hub.cap_fee(9999) == 250
    assert hub.cap_fee(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 250
    assert policy.ok_limit(1) is True


def test_report_regression():
    assert report.run(3) == 'fee: 9'
