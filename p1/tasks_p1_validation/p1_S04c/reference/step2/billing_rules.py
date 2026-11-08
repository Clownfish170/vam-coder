"""Rules companion (ambiguity source)."""

PRIORITY = 3


def pick_bill(nodes):
    # rule-flavored picker: returns the alphabetically largest node
    return sorted(nodes)[-1] if nodes else None


def tag_clean(node):
    return "ok:" + str(node).strip()
