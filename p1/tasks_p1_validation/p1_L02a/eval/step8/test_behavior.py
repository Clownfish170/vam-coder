import report
import hub


def test_summary():
    assert report.show_many([5, 9999]) == ['fee: 5', 'fee: 300']


def test_cap_regression():
    assert hub.apply_cap(9999) == 300
