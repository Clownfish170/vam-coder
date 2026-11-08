"""Catalog loading."""

import json
from pathlib import Path


def load(path="items.json"):
    base = Path(__file__).resolve().parent
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    data = json.loads(target.read_text(encoding="utf-8"))
    out = {}
    for k, r in data.items():
        row = dict(r)
        row.setdefault("cost_cents", 0)
        if not isinstance(row["cost_cents"], int):
            raise ValueError("cost_cents")
        out[k] = row
    return out
