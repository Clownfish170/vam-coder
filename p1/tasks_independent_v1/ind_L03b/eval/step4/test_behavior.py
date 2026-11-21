import catalog


def test_total():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    catalog.add_row("b", 7)
    assert catalog.total() == 12


def test_total_empty():
    catalog.ROWS.clear()
    assert catalog.total() == 0


def test_set_qty_regression():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    assert catalog.set_qty("a", 3) is True
    assert catalog.total() == 3
