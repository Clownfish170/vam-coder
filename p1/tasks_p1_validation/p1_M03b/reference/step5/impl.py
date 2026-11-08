"""Text joiner"""


def join_items(data, sep=", "):
    items = [str(x) for x in data if x is not None]
    return sep.join(items)
