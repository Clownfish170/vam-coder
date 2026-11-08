import report
import hub


def test_summary():
    assert report.tax_all([5, 9999]) == ['fee: 5', 'fee: 290']


def test_cap_regression():
    assert hub.cap_tax(9999) == 290
