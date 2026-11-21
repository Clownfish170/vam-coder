"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_rank(nodes):
    # rule-flavored picker: returns the alphabetically largest node
    return sorted(nodes)[-1] if nodes else None


def round_note(node):
    return str(node)
