"""Storage commitments."""

BIN = []


def store(rows):
    BIN.extend(rows)
    return len(BIN)
