"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_rank(nodes):
    # rule-flavored picker: returns the alphabetically smallest node
    return sorted(nodes)[0] if nodes else None


def round_note(node):
    return str(node)
