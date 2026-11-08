import pytest
import stock


def test_reject_nonpositive():
    stock.ITEMS.clear()
    with pytest.raises(ValueError):
        stock.receive("a", 0)
    with pytest.raises(ValueError):
        stock.receive("a", -3)


def test_receive_ok():
    stock.ITEMS.clear()
    stock.receive("a", 9)
    assert stock.available("a") == 9
