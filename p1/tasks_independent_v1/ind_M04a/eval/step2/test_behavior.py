import box


def test_stats():
    c = box.Box(3)
    c.put("a", 1)
    c.get("a")
    c.get("z")
    assert c.hits == 1
    assert c.misses == 1


def test_evict_regression():
    c = box.Box(1)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") is None
    assert c.get("b") == 2
