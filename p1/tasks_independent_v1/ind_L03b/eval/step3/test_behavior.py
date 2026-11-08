import catalog


def test_set_qty():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    assert catalog.set_qty("a", 12) is True
    assert catalog.find("a")["qty"] == 12


def test_set_qty_missing():
    catalog.ROWS.clear()
    assert catalog.set_qty("zz", 1) is False


def test_duplicate_regression():
    import pytest
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    with pytest.raises(ValueError):
        catalog.add_row("a", 9)
