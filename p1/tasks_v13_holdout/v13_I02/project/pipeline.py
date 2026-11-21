"""Processing pipeline."""


def run(item):
    return f"cat:{item}"


def run_all(items):
    return [run(i) for i in items]
