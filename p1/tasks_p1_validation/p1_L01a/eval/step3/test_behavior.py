import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 250


def test_chain_regression():
    assert hub.quote(-2) == 0
    assert store.put('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
