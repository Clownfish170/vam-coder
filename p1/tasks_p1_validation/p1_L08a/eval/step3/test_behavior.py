import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 290


def test_chain_regression():
    assert hub.compute(-2) == 0
    assert store.put_tax('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
