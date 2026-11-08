import report
import hub


def test_summary():
    assert report.emit_all([5, 9999]) == ['fee: 5', 'fee: 200']


def test_cap_regression():
    assert hub.bound(9999) == 200
