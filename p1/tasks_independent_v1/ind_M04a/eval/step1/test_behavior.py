import box


def test_evict_oldest():
    c = box.Box(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_overwrite_no_evict():
    c = box.Box(1)
    c.put("a", 1)
    c.put("a", 9)
    assert c.get("a") == 9
