"""Catalog loading."""

import json
from pathlib import Path


def load(path="items.json"):
    base = Path(__file__).resolve().parent
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    return json.loads(target.read_text(encoding="utf-8"))
