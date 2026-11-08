import store


def test_put_get():
    b = store.Bag()
    b.put("a", 1)
    b.put("b", 2)
    assert b.get("a") == 1
    assert b.get("missing") is None


def test_last_wins():
    b = store.Bag()
    b.put("a", 1)
    b.put("a", 9)
    assert b.get("a") == 9


def test_repr_swapped():
    b = store.Bag()
    assert isinstance(b.__dict__.get("data"), dict)
    assert "items" not in b.__dict__
