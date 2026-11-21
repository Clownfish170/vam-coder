import hub
import report


def test_cap_negative():
    assert hub.clamp_cost(-3) == 0
    assert hub.clamp_cost(9999) == 280


def test_summary_regression():
    assert report.entries([5, 9999]) == ['fee: 5', 'fee: 280']
