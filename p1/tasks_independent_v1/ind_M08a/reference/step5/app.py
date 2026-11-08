"""Tiny app."""

from registry import register, dispatch


def hello(arg):
    return f"hi {arg}"


def bye(arg):
    return f"bye {arg}"


register("hello", hello)
register("bye", bye)
