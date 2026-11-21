import box


def test_none_not_stored():
    c = box.Box(2)
    c.put("a", None)
    c.put("b", 1)
    assert c.get("a") is None
    assert c.misses == 1
    assert c.hits == 0
    c.put("a", 5)
    assert c.get("a") == 5


def test_peek_regression():
    c = box.Box(2)
    c.put("a", 1)
    assert c.peek("a") == 1
    assert c.hits == 0


def test_lru_regression():
    c = box.Box(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert c.get("a") == 1
