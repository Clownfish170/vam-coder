from geom import area


def line(w, h):
    return f"{area((w, h))} u2"


def total(dims):
    return sum(area(d) for d in dims)
