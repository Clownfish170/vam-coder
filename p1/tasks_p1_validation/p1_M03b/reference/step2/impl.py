"""Text joiner"""


def join_items(data, sep=", "):
    return sep.join(str(x) for x in data)
