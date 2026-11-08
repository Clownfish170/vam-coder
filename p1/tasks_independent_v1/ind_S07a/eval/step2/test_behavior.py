import store


def test_delete():
    b = store.Bag()
    b.put("a", 1)
    assert b.delete("a") is True
    assert b.get("a") is None
    assert b.delete("a") is False


def test_repr_regression():
    b = store.Bag()
    assert isinstance(b.__dict__.get("data"), dict)


def test_put_get_regression():
    b = store.Bag()
    b.put("x", 5)
    assert b.get("x") == 5
