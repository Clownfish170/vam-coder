"""Usage meter."""
import prices


USAGE = {}


def record(day, units):
    if units < 0:
        raise ValueError("units")
    USAGE[day] = USAGE.get(day, 0) + units


def total_units():
    return sum(USAGE.values())


def day_charge(day):
    usage = USAGE.get(day, 0)
    return max(usage - prices.FREE_QUOTA, 0) * prices.UNIT_PRICE


def days_over():
    return sorted(d for d in USAGE if USAGE[d] > prices.FREE_QUOTA)
