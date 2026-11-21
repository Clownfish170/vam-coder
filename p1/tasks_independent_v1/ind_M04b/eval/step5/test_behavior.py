import shelf


def test_none_ignored():
    s = shelf.Shelf(2)
    s.store("a", None)
    assert s.entries == []
    s.store("a", 5)
    assert s.fetch("a") == 5


def test_peek_regression():
    s = shelf.Shelf(2)
    s.store("a", 1)
    assert s.peek("a") == 1
    assert s.hits == 0


def test_lru_regression():
    s = shelf.Shelf(2)
    s.store("a", 1)
    s.store("b", 2)
    s.fetch("a")
    s.store("c", 3)
    assert s.fetch("a") == 1
