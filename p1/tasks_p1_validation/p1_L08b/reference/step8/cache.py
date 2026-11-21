"""Frame cache"""
from top import dispatch


def prime_f(x):
    return "k:" + str(x)


def prime_f_serve(n):
    return dispatch(n) + 1
