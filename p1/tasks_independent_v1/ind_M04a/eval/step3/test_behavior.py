import box


def test_lru_get_refresh():
    c = box.Box(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert c.get("a") == 1
    assert c.get("b") is None


def test_lru_put_refresh():
    c = box.Box(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 9)
    c.put("c", 3)
    assert c.get("a") == 9
    assert c.get("b") is None


def test_stats_regression():
    c = box.Box(2)
    c.put("a", 1)
    c.get("a")
    assert c.hits == 1
