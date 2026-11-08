"""Storage commitments."""

BIN = []


def store(rows):
    BIN.extend(rows)
    return len(BIN)


def commit(rows):
    kept = sum(1 for r in rows if r.get("qty", 0) > 0)
    return {"kept": kept, "rejected": len(rows) - kept}
