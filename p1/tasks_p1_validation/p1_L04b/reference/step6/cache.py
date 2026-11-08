"""Row cache"""
from top import flush


def warm_row(x):
    return "k:" + str(x)


def warm_row_serve(n):
    return flush(n) + 3
