"""配置加载：config/default.json → AppConfig；路径类配置由调用方覆盖。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .hashing import content_hash

DEFAULT_CONFIG_REL = Path("config") / "default.json"


@dataclass
class AppConfig:
    hash_algo: str = "blake3"
    closure_depth: int = 2
    simulate_kv: bool = True
    simulate_summary: bool = True
    budget_tokens: int = 4096
    kv_reuse_overhead_tokens: int = 32
    chars_per_token: int = 4
    supported_languages: dict[str, str] = field(
        default_factory=lambda: {".py": "python"}
    )
    db_path: str = "state/static_store.db"
    decision_log: str = "logs/decisions.jsonl"
    invalidation_log: str = "logs/invalidation_events.jsonl"

    @classmethod
    def from_dict(cls, raw: dict) -> "AppConfig":
        paths = raw.get("paths", {})
        known = {k: v for k, v in raw.items() if k != "paths"}
        cfg = cls(**known)
        cfg.db_path = paths.get("db", cfg.db_path)
        cfg.decision_log = paths.get("decision_log", cfg.decision_log)
        cfg.invalidation_log = paths.get("invalidation_log", cfg.invalidation_log)
        return cfg

    @classmethod
    def load(cls, path: str | Path | None = None) -> "AppConfig":
        """path 为空时按 cwd 查找 config/default.json；文件不存在则用默认值。"""
        if path is None:
            candidate = Path.cwd() / DEFAULT_CONFIG_REL
            if not candidate.is_file():
                return cls()
            path = candidate
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    def routing_dict(self) -> dict:
        """影响路由结果的字段（进 request_id / config_digest）。"""
        d = asdict(self)
        for k in ("db_path", "decision_log", "invalidation_log"):
            d.pop(k, None)
        return d

    def digest(self) -> str:
        payload = json.dumps(
            self.routing_dict(), sort_keys=True, ensure_ascii=False
        ).encode("utf-8")
        return content_hash(payload, self.hash_algo)[:16]
