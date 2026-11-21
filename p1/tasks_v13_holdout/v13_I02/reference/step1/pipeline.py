"""Processing pipeline."""


def run(item):
    return f"v2:{item}"


def run_all(items):
    return [run(i) for i in items]
