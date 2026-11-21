import report
import hub


def test_summary():
    assert report.lines_of([5, 9999]) == ['fee: 5', 'fee: 320']


def test_cap_regression():
    assert hub.cap_interest(9999) == 320
