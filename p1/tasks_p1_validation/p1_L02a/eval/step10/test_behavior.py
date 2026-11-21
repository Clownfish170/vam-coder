import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 500
    assert hub.apply_cap(9999) == 500
    assert hub.apply_cap(500) == 500
    assert hub.apply_cap(-3) == 0


def test_summary_follows_new_limit():
    assert report.show_many([9999]) == ['fee: 500']


def test_full_chain_regression():
    assert hub.price(3) == 12
    assert hub.clean(None) == '-'
    assert store.save('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.show(3) == 'fee: 12'
