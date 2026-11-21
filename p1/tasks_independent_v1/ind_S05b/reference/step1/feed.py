"""Feed parsing."""


class BadFeed(Exception):
    pass


def parse_line(line):
    parts = line.split(",")
    if len(parts) < 2:
        raise BadFeed("fields")
    return parts[0], parts[1]
