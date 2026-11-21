"""Token cache"""
from top import push


def prime_t(x):
    return "k:" + str(x)


def prime_t_serve(n):
    return push(n) + 1
