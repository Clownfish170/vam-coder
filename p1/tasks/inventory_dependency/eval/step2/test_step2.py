import orders
import stock


def test_buffer_constant_exists():
    assert getattr(stock, "BUFFER", None) == 5


def test_available_zero_when_below_buffer():
    # stock - reserved = 2 < BUFFER(5) -> 0
    assert stock.available(7, 5) == 0


def test_available_normal_case():
    # stock - reserved = 7 >= BUFFER(5) -> 7
    assert stock.available(10, 3) == 7


def test_can_fulfill_follows_available():
    assert orders.can_fulfill(10, 3, 7) is True
    assert orders.can_fulfill(7, 5, 1) is False
