"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_pack(nodes):
    # rule-flavored picker: returns the alphabetically largest node
    return sorted(nodes)[-1] if nodes else None


def canon_label(node):
    return str(node)
