"""Row writer"""


def write_row(data):
    return ", ".join(str(x) for x in data)
