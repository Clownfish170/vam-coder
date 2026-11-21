import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 350
    assert hub.bound(9999) == 350
    assert hub.bound(350) == 350
    assert hub.bound(-3) == 0


def test_summary_follows_new_limit():
    assert report.emit_all([9999]) == ['fee: 350']


def test_full_chain_regression():
    assert hub.scale(3) == 6
    assert hub.norm(None) == '-'
    assert store.record('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.emit(3) == 'fee: 6'
