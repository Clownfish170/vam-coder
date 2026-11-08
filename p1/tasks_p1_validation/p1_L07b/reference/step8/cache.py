"""Stats cache"""
from top import serve_s


def prime_s(x):
    return "k:" + str(x)


def prime_s_serve(n):
    return serve_s(n) + 2
