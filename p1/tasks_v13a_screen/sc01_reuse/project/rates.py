RATE = 3
LABEL = 'sc01'
TABLE = {'a': 1, 'b': 2, 'c': 3}


def lookup(key):
    return TABLE.get(key, 0)


def bulk_lookup(keys):
    return [lookup(k) for k in keys]


def dump_table():
    return dict(TABLE)


def reset_table():
    TABLE.clear()
    TABLE.update({'a': 1, 'b': 2, 'c': 3})
