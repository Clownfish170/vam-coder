"""Contact roll utilities."""

ROWS = [{"name": "ada", "team": "x"}, {"name": "bob", "team": "y"}]


def join_names(rows):
    return "|".join(r["name"] for r in rows)


def teams(rows):
    return sorted({r["team"] for r in rows})
