"""JSONL 实验日志（决策日志 + 失效事件日志），与源码/配置分离存放。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class JsonlLogger:
    """追加式 JSONL 写入器；path 为 None 时为 no-op（便于纯单测）。"""

    def __init__(self, path: str | Path | None):
        self.path = Path(path) if path is not None else None

    def emit(self, event: str, **payload) -> dict:
        record = {"ts": _now(), "event": event, **payload}
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                )
        return record

    @staticmethod
    def read_all(path: str | Path) -> list[dict]:
        p = Path(path)
        if not p.is_file():
            return []
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out
