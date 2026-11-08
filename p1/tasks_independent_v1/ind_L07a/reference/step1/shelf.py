"""Record shelf."""


RECORDS = []


def insert(rec):
    RECORDS.append(rec)


def find(name):
    for rec in RECORDS:
        if rec["name"] == name:
            return rec
    return None
