import shelf


def test_peek_quiet():
    s = shelf.Shelf(2)
    s.store("a", 1)
    s.store("b", 2)
    assert s.peek("a") == 1
    assert s.peek("z") is None
    assert s.hits == 0
    assert s.misses == 0
    assert s.entries[0][0] == "a"


def test_fetch_still_lru():
    s = shelf.Shelf(2)
    s.store("a", 1)
    s.store("b", 2)
    s.fetch("a")
    s.store("c", 3)
    assert s.fetch("a") == 1
