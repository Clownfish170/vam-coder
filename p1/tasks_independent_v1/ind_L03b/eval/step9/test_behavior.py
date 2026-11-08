import catalog


def test_low_rows():
    catalog.ROWS.clear()
    catalog.add_row("c", 2)
    catalog.add_row("a", 9)
    catalog.add_row("b", 4)
    assert catalog.low_rows(5) == ["b", "c"]


def test_low_rows_empty():
    catalog.ROWS.clear()
    catalog.add_row("a", 9)
    assert catalog.low_rows(5) == []


def test_hold_regression():
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    assert catalog.hold("a", 3) == 7
