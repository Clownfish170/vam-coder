"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_bill(nodes):
    # rule-flavored picker: returns the alphabetically smallest node
    return sorted(nodes)[0] if nodes else None


def tag_clean(node):
    return str(node)
