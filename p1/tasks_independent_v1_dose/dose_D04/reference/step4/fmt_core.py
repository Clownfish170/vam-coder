from fmt_strings import EMPTY, SEP


def join3(a, b, c):
    parts = [EMPTY if x is None else x for x in (a, b, c)]
    return parts[0] + SEP + parts[1] + SEP + parts[2]


def join_list(xs):
    items = [x for x in xs if x is not None]
    if not items:
        return EMPTY
    return SEP.join(items)
