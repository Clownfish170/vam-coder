import hub
import report


def test_cap_negative():
    assert hub.cap_tax(-3) == 0
    assert hub.cap_tax(9999) == 290


def test_summary_regression():
    assert report.tax_all([5, 9999]) == ['fee: 5', 'fee: 290']
