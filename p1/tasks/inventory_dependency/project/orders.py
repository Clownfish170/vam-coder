from stock import available


def can_fulfill(stock, reserved, quantity):
    """Whether the shop can fulfill an order of `quantity`."""
    return available(stock, reserved) >= quantity
