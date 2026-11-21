from route_table import ALIAS, DEFAULT_PATH


def resolve(key):
    if key in ALIAS:
        return ALIAS[key]
    return DEFAULT_PATH


def has_alias(key):
    return key in ALIAS
