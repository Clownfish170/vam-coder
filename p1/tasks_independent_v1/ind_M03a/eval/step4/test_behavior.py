import pytest

import order


def test_refund():
    assert order.advance("shipped", "refund") == "refunded"


def test_refunded_terminal():
    with pytest.raises(ValueError):
        order.advance("refunded", "pay")


def test_shipped_bad_action():
    with pytest.raises(ValueError):
        order.advance("shipped", "pay")
