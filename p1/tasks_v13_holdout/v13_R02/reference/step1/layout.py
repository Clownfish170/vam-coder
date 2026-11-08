"""Layout aggregation."""


def total_area(items):
    return sum(it.area() for it in items)


def place(item, dx, dy):
    return (dx, dy)
