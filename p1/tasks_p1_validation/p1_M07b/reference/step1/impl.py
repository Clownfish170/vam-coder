"""Row glue"""


def glue(data):
    return ", ".join(str(x) for x in data)
