"""Layout aggregation."""


def total_area(items):
    return sum(it.area() for it in items)


def place(item, dx, dy):
    return (dx, dy)


def scaled_areas(items, factor):
    out = []
    for it in items:
        it.scale(factor)
        out.append(it.area())
    return out
