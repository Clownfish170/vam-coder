import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 420
    assert hub.cap_rent(9999) == 420
    assert hub.cap_rent(420) == 420
    assert hub.cap_rent(-3) == 0


def test_summary_follows_new_limit():
    assert report.descs([9999]) == ['fee: 420']


def test_full_chain_regression():
    assert hub.fee_of(3) == 9
    assert hub.scrub(None) == '-'
    assert store.log('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.desc_of(3) == 'fee: 9'
