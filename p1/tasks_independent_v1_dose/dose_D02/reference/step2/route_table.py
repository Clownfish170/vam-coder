DEFAULT_PATH = '/home'
ALIAS = {'h': '/alias_home'}


def default():
    return DEFAULT_PATH


def lookup(k):
    return ALIAS.get(k)
