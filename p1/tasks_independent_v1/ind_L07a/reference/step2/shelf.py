"""Record shelf."""


RECORDS = []


def insert(rec):
    if any(r["name"] == rec["name"] for r in RECORDS):
        raise ValueError("name")
    RECORDS.append(rec)


def find(name):
    for rec in RECORDS:
        if rec["name"] == name:
            return rec
    return None
