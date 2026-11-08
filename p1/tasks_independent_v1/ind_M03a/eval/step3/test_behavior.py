import pytest

import order


def test_terminal_raises():
    with pytest.raises(ValueError):
        order.advance("shipped", "pay")
    with pytest.raises(ValueError):
        order.advance("cancelled", "pay")


def test_normal_regression():
    assert order.advance("new", "pay") == "paid"
