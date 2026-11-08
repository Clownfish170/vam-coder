import catalog


def test_find():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    catalog.add_row("b", 7)
    row = catalog.find("b")
    assert row["qty"] == 7


def test_find_missing():
    catalog.ROWS.clear()
    assert catalog.find("zz") is None


def test_add_regression():
    catalog.ROWS.clear()
    catalog.add_row("a", 1)
    assert catalog.ROWS == [{"sku": "a", "qty": 1}]
