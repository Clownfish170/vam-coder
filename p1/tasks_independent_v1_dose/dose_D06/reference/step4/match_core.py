from match_pat import PREFIX, SUFFIX


def match(s):
    if s is None or s == '':
        return False
    return s.startswith(PREFIX) and s.endswith(SUFFIX)


def strip_affix(s):
    body = s
    if body.startswith(PREFIX):
        body = body[len(PREFIX):]
    if body.endswith(SUFFIX):
        body = body[: -len(SUFFIX)]
    return body
