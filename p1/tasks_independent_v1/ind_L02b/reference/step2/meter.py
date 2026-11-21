"""Usage meter."""


USAGE = {}


def record(day, units):
    if units < 0:
        raise ValueError("units")
    USAGE[day] = USAGE.get(day, 0) + units


def total_units():
    return sum(USAGE.values())
