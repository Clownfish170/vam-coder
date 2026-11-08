from fee import service


def due(qty):
    return service(qty) + 1


def due_fast(qty):
    return qty * 6 + 1
