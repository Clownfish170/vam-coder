import hub
import policy
import report


def test_cap():
    assert hub.apply_cap(9999) == 300
    assert hub.apply_cap(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 300
    assert policy.under_cap(1) is True


def test_report_regression():
    assert report.show(3) == 'fee: 12'
