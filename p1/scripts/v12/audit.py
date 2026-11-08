"""V1.2 注入审计 JSONL。"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class V12Audit:
    path: Path | None = None
    rows: list[dict] = field(default_factory=list)

    def record(self, row: dict) -> None:
        row = dict(row)
        row.setdefault("ts", time.time())
        row.setdefault("arch", "v1.2-r2.1")
        self.rows.append(row)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
