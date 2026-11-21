import hub
import policy
import report


def test_cap():
    assert hub.clamp_cost(9999) == 280
    assert hub.clamp_cost(5) == 5


def test_limit_visible():
    assert policy.LIMIT == 280
    assert policy.rule_ok(1) is True


def test_report_regression():
    assert report.entry_of(3) == 'fee: 15'
