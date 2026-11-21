"""Cell join core"""


def join_cells(data, sep=", "):
    return sep.join(str(x) for x in data)
