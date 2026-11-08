import hub
import report


def test_run():
    assert report.tax_run(3) == 'fee: 12'


def test_trim_regression():
    assert hub.fix_tax(None) == '-'
