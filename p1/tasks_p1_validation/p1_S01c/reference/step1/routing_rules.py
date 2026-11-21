"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_route(nodes):
    # rule-flavored picker: returns the alphabetically largest node
    return sorted(nodes)[-1] if nodes else None


def normalize(node):
    return str(node)
