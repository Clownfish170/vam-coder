"""Tiny app."""

from registry import register, dispatch


def hello(arg):
    return f"hi {arg}"


register("hello", hello)
