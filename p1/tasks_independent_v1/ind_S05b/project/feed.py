"""Feed parsing."""


def parse_line(line):
    parts = line.split(",")
    return parts[0], parts[1]
