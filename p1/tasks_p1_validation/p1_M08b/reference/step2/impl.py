"""Seq builder"""


def build_seq(data, sep=", "):
    return sep.join(str(x) for x in data)
