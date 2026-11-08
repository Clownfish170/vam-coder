import shelf


def test_stats():
    s = shelf.Shelf(3)
    s.store("a", 1)
    s.fetch("a")
    s.fetch("z")
    assert s.hits == 1
    assert s.misses == 1


def test_store_regression():
    s = shelf.Shelf(1)
    s.store("a", 1)
    s.store("b", 2)
    assert s.fetch("a") is None
    assert s.fetch("b") == 2
