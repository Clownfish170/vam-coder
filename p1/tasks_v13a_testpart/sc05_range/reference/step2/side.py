SIDE = 1
SIDE_NAME = 'sc05'


def side_fn():
    return SIDE


def side_label():
    return SIDE_NAME


def side_scale(x):
    return x * SIDE


def side_report(x):
    return f'{SIDE_NAME}:{side_scale(x)}'
