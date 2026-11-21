"""Record loading."""

import json
from pathlib import Path


def defaults():
    return {"full_name": "", "age": 0}


def load(path="people.json"):
    base = Path(__file__).resolve().parent
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    rows = json.loads(target.read_text(encoding="utf-8"))
    out = []
    for r in rows:
        row = dict(defaults())
        row.update(r)
        if not isinstance(row["age"], int):
            raise ValueError("age")
        out.append(row)
    return out
