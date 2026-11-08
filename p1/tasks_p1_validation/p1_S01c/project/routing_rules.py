"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_route(nodes):
    # rule-flavored picker: returns the alphabetically smallest node
    return sorted(nodes)[0] if nodes else None


def normalize(node):
    return str(node)
