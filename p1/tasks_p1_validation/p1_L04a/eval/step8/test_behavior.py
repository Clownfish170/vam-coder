import report
import hub


def test_summary():
    assert report.entries([5, 9999]) == ['fee: 5', 'fee: 280']


def test_cap_regression():
    assert hub.clamp_cost(9999) == 280
