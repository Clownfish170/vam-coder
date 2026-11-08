import store, use


def test_put():
    assert store.put({}, 'k', 1) == 1


def test_seed():
    assert use.seed() == {'a': 1}
