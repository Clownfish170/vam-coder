"""Usage meter."""


USAGE = {}


def record(day, units):
    USAGE[day] = USAGE.get(day, 0) + units
