import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 400
    assert hub.cap_fee(9999) == 400
    assert hub.cap_fee(400) == 400
    assert hub.cap_fee(-3) == 0


def test_summary_follows_new_limit():
    assert report.summary([9999]) == ['fee: 400']


def test_full_chain_regression():
    assert hub.quote(3) == 9
    assert hub.trim(None) == '-'
    assert store.put('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.run(3) == 'fee: 9'
