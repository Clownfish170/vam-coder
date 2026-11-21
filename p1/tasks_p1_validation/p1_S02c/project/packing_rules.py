"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_pack(nodes):
    # rule-flavored picker: returns the alphabetically smallest node
    return sorted(nodes)[0] if nodes else None


def canon_label(node):
    return str(node)
