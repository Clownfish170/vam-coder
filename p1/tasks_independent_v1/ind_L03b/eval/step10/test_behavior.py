import pytest
import caps
import catalog
import front


def test_cap_revised():
    assert caps.MAX_HOLD == 2
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    with pytest.raises(ValueError):
        catalog.hold("a", 3)


def test_full_chain():
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    catalog.add_row("b", 1)
    assert catalog.find("a")["qty"] == 10
    assert catalog.total() == 11
    assert catalog.hold("a", 2) == 8
    assert front.stock_line("a") == "sku=a qty=8"
    assert catalog.low_rows(5) == ["b"]
