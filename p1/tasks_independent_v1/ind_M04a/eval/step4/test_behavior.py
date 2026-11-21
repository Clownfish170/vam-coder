import box


def test_peek_no_stats():
    c = box.Box(2)
    c.put("a", 1)
    assert c.peek("a") == 1
    assert c.peek("z") is None
    assert c.hits == 0
    assert c.misses == 0


def test_peek_no_order_change():
    c = box.Box(2)
    c.put("a", 1)
    c.put("b", 2)
    c.peek("a")
    c.put("c", 3)
    assert c.get("a") is None
    assert c.get("b") == 2


def test_get_stats_regression():
    c = box.Box(2)
    c.put("a", 1)
    c.get("a")
    assert c.hits == 1
