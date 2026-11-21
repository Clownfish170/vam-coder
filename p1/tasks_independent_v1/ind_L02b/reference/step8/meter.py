"""Usage meter."""
import prices


USAGE = {}


def record(day, units):
    if units < 0:
        raise ValueError("units")
    if len(day) != 10 or day[4] != "-" or day[7] != "-":
        raise ValueError("day")
    if not (day[:4].isdigit() and day[5:7].isdigit() and day[8:10].isdigit()):
        raise ValueError("day")
    USAGE[day] = USAGE.get(day, 0) + units


def total_units():
    return sum(USAGE.values())


def day_charge(day):
    usage = USAGE.get(day, 0)
    return max(usage - prices.FREE_QUOTA, 0) * prices.UNIT_PRICE


def days_over():
    return sorted(d for d in USAGE if USAGE[d] > prices.FREE_QUOTA)


def peak():
    if not USAGE:
        return None
    best = max(USAGE.values())
    return min(d for d in USAGE if USAGE[d] == best)
