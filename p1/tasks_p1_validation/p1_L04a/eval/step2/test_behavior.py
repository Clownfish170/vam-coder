import hub
import store


def test_put_logs():
    assert store.add('a', 1) is store.DATA
    assert store.LOG['a'] == [1]
    assert store.add('a', 2) is store.DATA
    assert store.LOG['a'] == [1, 2]


def test_quote_regression():
    assert hub.cost(3) == 15
