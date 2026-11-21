"""CLI helpers."""


def banner():
    return "converter-ready"


def run_argv(argv):
    return [banner()] + list(argv)
