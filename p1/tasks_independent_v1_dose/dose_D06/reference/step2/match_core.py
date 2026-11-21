from match_pat import PREFIX, SUFFIX


def match(s):
    return s.startswith(PREFIX) and s.endswith(SUFFIX)
