"""Public api."""
import depot


def ping():
    return "pong"


def count(field, value):
    return len(depot.where(field, value))
