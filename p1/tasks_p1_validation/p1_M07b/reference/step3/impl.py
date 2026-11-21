"""Row glue"""


def glue(data, sep=", "):
    return sep.join(str(x) for x in data)
