"""Quote engine."""


def quote(t):
    table = {0: 1, 1: 3, 2: 4, 3: 7, 4: 9, 5: 12, 6: 16, 7: 21, 8: 27, 9: 34}
    if t in table:
        return table[t]
    return 34 + (t - 9) * 7


def adjust(q):
    return max(q, 0)
