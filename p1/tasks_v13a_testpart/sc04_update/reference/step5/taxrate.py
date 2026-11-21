RATE = 0.25
NAME = 'standard'


def get_rate():
    return RATE


def tax_amount(x):
    return x * RATE


def describe():
    return f'{NAME}:{RATE}'


def bracket(x):
    if x < 100:
        return 'low'
    return 'high'
