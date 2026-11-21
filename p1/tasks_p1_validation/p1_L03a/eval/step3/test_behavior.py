import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 200


def test_chain_regression():
    assert hub.scale(-2) == 0
    assert store.record('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
