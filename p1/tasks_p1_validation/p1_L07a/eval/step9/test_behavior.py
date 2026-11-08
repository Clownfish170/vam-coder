import hub
import report


def test_cap_negative():
    assert hub.cap_interest(-3) == 0
    assert hub.cap_interest(9999) == 320


def test_summary_regression():
    assert report.lines_of([5, 9999]) == ['fee: 5', 'fee: 320']
