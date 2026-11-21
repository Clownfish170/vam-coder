from route_table import ALIAS, DEFAULT_PATH


def resolve(key):
    if key in ALIAS:
        return ALIAS[key]
    return None


def has_alias(key):
    if not isinstance(key, str) or len(key) < 2:
        return False
    return key in ALIAS
