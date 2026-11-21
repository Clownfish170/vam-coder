from fmt_strings import EMPTY, SEP


def join3(a, b, c):
    parts = [EMPTY if x is None else x for x in (a, b, c)]
    return SEP.join(parts)


def join_list(xs):
    items = [x for x in xs if x is not None]
    if not items:
        return (EMPTY, 0)
    return (SEP.join(items), len(items))
