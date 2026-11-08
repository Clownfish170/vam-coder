import pytest
import catalog


def test_hold_zero():
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    with pytest.raises(ValueError):
        catalog.hold("a", 0)


def test_hold_negative():
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    with pytest.raises(ValueError):
        catalog.hold("a", -1)


def test_hold_ok_regression():
    catalog.ROWS.clear()
    catalog.add_row("a", 10)
    assert catalog.hold("a", 3) == 7
