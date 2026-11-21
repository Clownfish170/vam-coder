"""Record shelf."""


RECORDS = []


def insert(rec):
    if any(r["name"] == rec["name"] for r in RECORDS):
        raise ValueError("name")
    if rec["score"] < 0 or rec["score"] > 100:
        raise ValueError("score")
    RECORDS.append(rec)


def find(name):
    for rec in RECORDS:
        if rec["name"] == name:
            return rec
    return None


def filter_by(min_score):
    return [r for r in RECORDS if r["score"] >= min_score]


def page(offset, limit):
    return RECORDS[offset:offset + limit]
