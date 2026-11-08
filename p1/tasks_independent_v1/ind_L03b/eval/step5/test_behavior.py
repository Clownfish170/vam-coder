import front
import catalog


def test_stock_line():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    assert front.stock_line("a") == "sku=a qty=5"


def test_stock_line_missing():
    catalog.ROWS.clear()
    assert front.stock_line("zz") == "sku=zz qty=missing"


def test_greeting_regression():
    assert front.greeting() == "welcome"


def test_total_regression():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    assert catalog.total() == 5
