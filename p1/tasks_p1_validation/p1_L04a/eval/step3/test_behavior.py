import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 280


def test_chain_regression():
    assert hub.cost(-2) == 0
    assert store.add('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
