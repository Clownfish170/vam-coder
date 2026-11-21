import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 450
    assert hub.clamp_cost(9999) == 450
    assert hub.clamp_cost(450) == 450
    assert hub.clamp_cost(-3) == 0


def test_summary_follows_new_limit():
    assert report.entries([9999]) == ['fee: 450']


def test_full_chain_regression():
    assert hub.cost(3) == 15
    assert hub.tidy(None) == '-'
    assert store.add('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.entry_of(3) == 'fee: 15'
