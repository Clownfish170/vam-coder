"""CLI."""


from engine import evaluate


def run(x):
    return evaluate(x)


def double_run(x):
    return run(x) + run(x + 1)
