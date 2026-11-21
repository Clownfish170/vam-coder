"""Key cache"""
from top import drive


def arm(x):
    return "k:" + str(x)


def arm_serve(n):
    return drive(n) + 2
