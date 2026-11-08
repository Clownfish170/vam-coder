import pytest
import catalog


def test_hold_ok():
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    assert catalog.hold("a", 3) == 7
    assert catalog.find("a")["qty"] == 7


def test_hold_over_cap():
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    with pytest.raises(ValueError):
        catalog.hold("a", 7)


def test_hold_missing_row():
    catalog.ROWS.clear()
    with pytest.raises(KeyError):
        catalog.hold("zz", 1)


def test_total_regression():
    catalog.ROWS.clear()
    catalog.add_row("a", 5)
    assert catalog.total() == 5
