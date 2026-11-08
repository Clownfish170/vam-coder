"""Cli front."""
import panel


def banner():
    return "cli"


def call(name, *args):
    try:
        return panel.run(name, *args)
    except KeyError:
        return None
