import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 320


def test_chain_regression():
    assert hub.interest(-2) == 0
    assert store.save_i('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
