"""Row writer"""


def write_row(data, sep=", "):
    return sep.join(str(x) for x in data)
