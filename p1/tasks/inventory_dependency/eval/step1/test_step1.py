import orders
import stock


def test_available_subtracts_reserved():
    assert stock.available(10, 3) == 7


def test_available_zero_floor():
    # step1 语义是纯减法（零下限在 step2 引入）
    assert stock.available(2, 5) == -3


def test_can_fulfill_uses_available():
    assert orders.can_fulfill(10, 3, 7) is True
    assert orders.can_fulfill(10, 3, 8) is False
