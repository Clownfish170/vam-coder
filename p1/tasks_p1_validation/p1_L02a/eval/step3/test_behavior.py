import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 300


def test_chain_regression():
    assert hub.price(-2) == 0
    assert store.save('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
