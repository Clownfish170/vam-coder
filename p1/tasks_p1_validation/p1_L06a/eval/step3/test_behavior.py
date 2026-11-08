import hub
import store
import policy


def test_limit_updated():
    assert policy.LIMIT == 260


def test_chain_regression():
    assert hub.fee_of(-2) == 0
    assert store.log('b', 9) is store.DATA
    assert store.LOG['b'] == [9]
