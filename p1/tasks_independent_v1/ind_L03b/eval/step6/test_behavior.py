import caps
import front
import catalog


def test_cap_updated():
    assert caps.MAX_HOLD == 6


def test_stock_line_regression():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    assert front.stock_line("a") == "sku=a qty=5"
