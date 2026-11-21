import hub
import report


def test_cap_negative():
    assert hub.bound(-3) == 0
    assert hub.bound(9999) == 200


def test_summary_regression():
    assert report.emit_all([5, 9999]) == ['fee: 5', 'fee: 200']
