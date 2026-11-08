import shelf


def test_lru_fetch_moves_to_end():
    s = shelf.Shelf(2)
    s.store("a", 1)
    s.store("b", 2)
    s.fetch("a")
    s.store("c", 3)
    assert s.fetch("a") == 1
    assert s.fetch("b") is None


def test_stats_regression():
    s = shelf.Shelf(2)
    s.store("a", 1)
    s.fetch("a")
    assert s.hits == 1
    assert s.fetch("z") is None
    assert s.misses == 1
