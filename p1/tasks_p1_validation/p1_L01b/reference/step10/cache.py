"""Result cache"""
from top import serve


def warm(x):
    return "k:" + str(x)


def warm_serve(n):
    return serve(n) + 1
