import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 380
    assert hub.cap_pts(9999) == 380
    assert hub.cap_pts(380) == 380
    assert hub.cap_pts(-3) == 0


def test_summary_follows_new_limit():
    assert report.labels([9999]) == ['fee: 380']


def test_full_chain_regression():
    assert hub.points(3) == 18
    assert hub.fix(None) == '-'
    assert store.put_row('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.label_for(3) == 'fee: 18'
