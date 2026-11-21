"""Stream printer"""


def print_stream(data, sep=", "):
    return sep.join(str(x) for x in data)
