import pytest
import catalog


def test_duplicate_rejected():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    with pytest.raises(ValueError):
        catalog.add_row("a", 9)
    assert catalog.find("a")["qty"] == 5


def test_new_sku_ok():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    catalog.add_row("b", 6)
    assert len(catalog.ROWS) == 2
