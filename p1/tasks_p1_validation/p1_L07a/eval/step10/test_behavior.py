import hub
import policy
import report
import store


def test_limit_v2():
    assert policy.LIMIT == 480
    assert hub.cap_interest(9999) == 480
    assert hub.cap_interest(480) == 480
    assert hub.cap_interest(-3) == 0


def test_summary_follows_new_limit():
    assert report.lines_of([9999]) == ['fee: 480']


def test_full_chain_regression():
    assert hub.interest(3) == 6
    assert hub.tidy_i(None) == '-'
    assert store.save_i('q', 1) is store.DATA
    assert store.LOG['q'] == [1]
    assert report.line_of(3) == 'fee: 6'
