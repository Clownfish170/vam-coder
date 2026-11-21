MARGIN = 0.20
NAME = 'sc02'
CAPS = {'max_n': 100, 'min_n': 0}


def get_margin():
    return MARGIN


def get_caps():
    return dict(CAPS)


def describe():
    return f'{NAME}:margin={MARGIN}'
