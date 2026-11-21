import hub
import report


def test_cap_negative():
    assert hub.apply_cap(-3) == 0
    assert hub.apply_cap(9999) == 300


def test_summary_regression():
    assert report.show_many([5, 9999]) == ['fee: 5', 'fee: 300']
