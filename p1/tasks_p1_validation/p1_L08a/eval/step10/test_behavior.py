import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 460
    assert hub.cap_tax(9999) == 460
    assert hub.cap_tax(460) == 460
    assert hub.cap_tax(-3) == 0


def test_summary_follows_new_limit():
    assert report.tax_all([9999]) == ['fee: 460']


def test_full_chain_regression():
    assert hub.compute(3) == 12
    assert hub.fix_tax(None) == '-'
    assert store.put_tax('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.tax_run(3) == 'fee: 12'
