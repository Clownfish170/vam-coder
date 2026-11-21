import shelf


def test_store_evict():
    s = shelf.Shelf(2)
    s.store("a", 1)
    s.store("b", 2)
    s.store("c", 3)
    assert s.fetch("a") is None
    assert s.fetch("b") == 2
    assert s.fetch("c") == 3


def test_store_overwrite():
    s = shelf.Shelf(2)
    s.store("a", 1)
    s.store("a", 9)
    assert s.fetch("a") == 9
    assert len(s.entries) == 1
