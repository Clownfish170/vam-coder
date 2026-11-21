"""Feed parsing."""


class BadFeed(Exception):
    pass


def parse_line(line):
    parts = line.split(",")
    if len(parts) < 2:
        raise BadFeed("fields")
    key, value = parts[0].strip(), parts[1].strip()
    if not key or not value:
        raise BadFeed("empty")
    return key, value
