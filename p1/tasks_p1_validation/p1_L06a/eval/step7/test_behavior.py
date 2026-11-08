import hub
import policy
import report


def test_cap():
    assert hub.cap_rent(9999) == 260
    assert hub.cap_rent(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 260
    assert policy.allowed(1) is True


def test_report_regression():
    assert report.desc_of(3) == 'fee: 9'
