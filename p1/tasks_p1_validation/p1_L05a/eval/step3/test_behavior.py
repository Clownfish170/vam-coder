import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 220


def test_chain_regression():
    assert hub.points(-2) == 0
    assert store.put_row('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
