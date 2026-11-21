from match_pat import PREFIX, SUFFIX


def match(s):
    if s is None or s == '':
        return False
    return s.startswith(PREFIX) and s.endswith(SUFFIX)


def strip_affix(s):
    if not isinstance(s, str):
        return s
    if not match(s):
        return s
    body = s[len(PREFIX):]
    return body[: -len(SUFFIX)]
