import hub
import policy
import report


def test_cap():
    assert hub.cap_tax(9999) == 290
    assert hub.cap_tax(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 290
    assert policy.tax_ok(1) is True


def test_report_regression():
    assert report.tax_run(3) == 'fee: 12'
