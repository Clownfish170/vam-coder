"""注入审计与成本账本（JSONL / 可汇总 dict）。"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CostLedger:
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_total: int = 0
    cost_index_ms: float = 0.0
    cost_route_ms: float = 0.0
    cost_assemble_ms: float = 0.0
    cost_fallback_events: int = 0
    injected_chars: int = 0
    omitted_chars_est: int = 0
    verified_safe_omission_files: int = 0
    latency_model_ms: float = 0.0
    notes: list[str] = field(default_factory=list)

    def add_step(
        self,
        *,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        index_ms: float = 0.0,
        route_ms: float = 0.0,
        assemble_ms: float = 0.0,
        fallback_events: int = 0,
        injected_chars: int = 0,
        omitted_chars_est: int = 0,
        verified_safe_omission_files: int = 0,
        model_latency_ms: float = 0.0,
    ) -> None:
        self.tokens_prompt += int(prompt_tokens or 0)
        self.tokens_completion += int(completion_tokens or 0)
        self.tokens_total += int(total_tokens or 0)
        self.cost_index_ms += float(index_ms or 0)
        self.cost_route_ms += float(route_ms or 0)
        self.cost_assemble_ms += float(assemble_ms or 0)
        self.cost_fallback_events += int(fallback_events or 0)
        self.injected_chars += int(injected_chars or 0)
        self.omitted_chars_est += int(omitted_chars_est or 0)
        self.verified_safe_omission_files += int(verified_safe_omission_files or 0)
        self.latency_model_ms += float(model_latency_ms or 0)

    def to_dict(self) -> dict:
        return {
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "tokens_total": self.tokens_total,
            "cost_index_ms": round(self.cost_index_ms, 3),
            "cost_route_ms": round(self.cost_route_ms, 3),
            "cost_assemble_ms": round(self.cost_assemble_ms, 3),
            "cost_fallback_events": self.cost_fallback_events,
            "injected_chars": self.injected_chars,
            "omitted_chars_est": self.omitted_chars_est,
            "verified_safe_omission_files": self.verified_safe_omission_files,
            "latency_model_ms": round(self.latency_model_ms, 3),
        }


@dataclass
class InjectionAudit:
    path: Path | None = None
    rows: list[dict] = field(default_factory=list)

    def record(self, row: dict) -> None:
        row = dict(row)
        row.setdefault("ts", time.time())
        self.rows.append(row)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def last(self) -> dict | None:
        return self.rows[-1] if self.rows else None
