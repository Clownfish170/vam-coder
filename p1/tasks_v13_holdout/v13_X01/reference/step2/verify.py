"""Row verification."""


def check(row):
    return row.get("qty", 0) > 0


def errors(rows):
    return [r for r in rows if not check(r)]
