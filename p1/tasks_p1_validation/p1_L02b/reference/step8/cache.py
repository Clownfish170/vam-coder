"""Unit cache"""
from top import handle


def prime(x):
    return "k:" + str(x)


def prime_serve(n):
    return handle(n) + 2
