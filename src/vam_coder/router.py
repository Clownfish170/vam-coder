"""规则路由器（无训练）：REUSE_KV / COMPRESS / EXPAND / DROP。

逐条目规则（优先级从上到下）：
1. validity=tombstoned → DROP   （对象已不存在）
2. validity!=valid     → EXPAND （stale/unverified 强制降级，REUSE_KV 被禁止）
3. 预算超限 & 有摘要   → COMPRESS（pass 2）
4. kv_ptr 可用(模拟)   → REUSE_KV
5. 否则                → EXPAND
全局：装配预估 tokens > budget → 按 keep-score =
      validity_rank / (est_tokens+1) 升序逐级降级
      （valid: REUSE_KV/EXPAND→COMPRESS→DROP；非 valid: EXPAND→DROP），
      直到满足预算。动态层（当前指令/最新报错）保护不在本阶段范围。

【动作语义】本路由器只**输出动作决策**：
- EXPAND = “决定重新读取完整源码”这一路由决策；P0 不实际执行文件读取、
  上下文装配、模型推理或 KV 复用（not implemented）。
- 能力边界见 CAPABILITY_STATUS：每项标注 implemented / simulated /
  not_implemented，同时写入决策日志。
- KV 缓存为模拟（kv_ptr 形如 sim://…，不落真实张量），见 README。
"""

from __future__ import annotations

from .config import AppConfig
from .hashing import content_hash
from .logging_util import JsonlLogger
from .models import (
    Action,
    MemoryEntry,
    RouteDecision,
    RouteRequest,
    RouteResult,
    Validity,
)

# 能力边界（写入决策日志，供验收核对）
CAPABILITY_STATUS: dict[str, str] = {
    "symbol_index": "implemented",
    "content_hash_versioning": "implemented",
    "dependency_invalidation_closure": "implemented",
    "tombstone": "implemented",
    "rule_routing_decision": "implemented",
    "request_decision_logging": "implemented",
    "kv_cache_reuse": "simulated",
    "summary_generation": "simulated",
    "token_estimation": "simulated",
    "expand_source_read_and_assembly": "not_implemented",
    "model_inference": "not_implemented",
    "model_summary_generation": "not_implemented",
}

_VALIDITY_RANK = {
    Validity.VALID.value: 3,
    Validity.UNVERIFIED.value: 2,
    Validity.STALE.value: 1,
    Validity.TOMBSTONED.value: 0,
}


class RuleRouter:
    def __init__(self, config: AppConfig | None = None,
                 logger: JsonlLogger | None = None):
        self.config = config or AppConfig()
        self.logger = logger or JsonlLogger(None)

    # ---------- 估算 ----------
    def _est(self, entry: MemoryEntry, action: str) -> int:
        cfg = self.config
        if action == Action.DROP.value:
            return 0
        if action == Action.REUSE_KV.value:
            return cfg.kv_reuse_overhead_tokens
        if action == Action.COMPRESS.value:
            text = entry.summary or ""
            return max(1, len(text) // cfg.chars_per_token)
        return max(1, entry.size_bytes // cfg.chars_per_token)

    # ---------- 逐条目门控 ----------
    _EXPAND_NOTE = (
        "EXPAND is a routing decision only: P0 does not read/assemble "
        "source, run inference, or reuse KV (not implemented)",
    )

    def _gated(self, entry: MemoryEntry) -> tuple[str, list[str]]:
        v = entry.validity
        if v == Validity.TOMBSTONED.value:
            return Action.DROP.value, [
                "validity=tombstoned: symbol deleted/renamed, "
                "not a valid object → DROP",
            ]
        if v == Validity.STALE.value:
            return Action.EXPAND.value, [
                "validity=stale: content_hash basis differs from current "
                "source → REUSE_KV forbidden",
                "restore protocol: EXPAND (re-read full source)",
                self._EXPAND_NOTE[0],
            ]
        if v == Validity.UNVERIFIED.value:
            return Action.EXPAND.value, [
                "validity=unverified: dependency closure changed → "
                "REUSE_KV forbidden",
                "restore protocol: EXPAND or rehash-verify first",
                self._EXPAND_NOTE[0],
            ]
        # valid
        if entry.kv_ptr and self.config.simulate_kv:
            return Action.REUSE_KV.value, [
                "validity=valid",
                f"kv_ptr available ({entry.kv_ptr}); prefix compat=simulated",
                "kv reuse enabled in config (simulate_kv=true)",
            ]
        reasons = ["validity=valid"]
        if not entry.kv_ptr:
            reasons.append("kv_ptr missing → REUSE_KV unavailable")
        if not self.config.simulate_kv:
            reasons.append("simulate_kv=false → real-KV path not implemented "
                           "in P0, fall back EXPAND")
        reasons.append("fallback EXPAND (re-read full source)")
        reasons.append(self._EXPAND_NOTE[0])
        return Action.EXPAND.value, reasons

    # ---------- 主入口 ----------
    def route(self, request: RouteRequest) -> RouteResult:
        cfg = self.config
        budget = request.budget_tokens or cfg.budget_tokens
        entries = sorted(request.entries, key=lambda e: e.symbol_id)

        decisions: list[RouteDecision] = []
        for e in entries:
            action, reasons = self._gated(e)
            decisions.append(
                RouteDecision(
                    symbol_id=e.symbol_id,
                    action=action,
                    validity=e.validity,
                    est_tokens=self._est(e, action),
                    reasons=reasons,
                )
            )

        by_id = {e.symbol_id: e for e in entries}
        total = sum(d.est_tokens for d in decisions)

        # pass 2：预算紧张 → valid 的 EXPAND 降为 COMPRESS（有摘要时）
        if total > budget:
            for d in sorted(decisions, key=lambda x: x.symbol_id):
                if d.action != Action.EXPAND.value:
                    continue
                e = by_id[d.symbol_id]
                if e.validity == Validity.VALID.value and e.summary:
                    d.action = Action.COMPRESS.value
                    d.est_tokens = self._est(e, d.action)
                    d.reasons.append(
                        f"budget tight (est {total} > {budget}): "
                        "EXPAND→COMPRESS using stored summary"
                    )
                    total = sum(x.est_tokens for x in decisions)

        # pass 3：仍超预算 → 按 keep-score 升序逐级降级
        while total > budget:
            candidates = [d for d in decisions if d.action != Action.DROP.value]
            if not candidates:
                break

            def victim_key(d: RouteDecision) -> tuple[float, str]:
                score = _VALIDITY_RANK[d.validity] / (d.est_tokens + 1)
                return (score, d.symbol_id)

            d = min(candidates, key=victim_key)
            e = by_id[d.symbol_id]
            old = d.action
            if d.validity == Validity.VALID.value:
                if old in (Action.REUSE_KV.value, Action.EXPAND.value,
                           Action.COMPRESS.value):
                    if old != Action.COMPRESS.value and e.summary:
                        d.action = Action.COMPRESS.value
                        d.reasons.append(
                            f"budget over ({total} > {budget}): "
                            f"{old}→COMPRESS (downgrade chain)"
                        )
                    else:
                        d.action = Action.DROP.value
                        d.reasons.append(
                            f"budget over ({total} > {budget}): "
                            f"{old}→DROP (downgrade chain, no summary)"
                        )
            else:
                # 非 valid：直接丢弃（不可信摘要不再进上下文）
                d.action = Action.DROP.value
                d.reasons.append(
                    f"budget over ({total} > {budget}): {old}→DROP "
                    "(invalid entry dropped first)"
                )
            d.est_tokens = self._est(e, d.action)
            total = sum(x.est_tokens for x in decisions)

        for d in decisions:
            if not d.reasons:
                d.reasons.append("default: no rule matched → DROP")
            d.reasons.append(f"final action={d.action}, est_tokens={d.est_tokens}")

        # request_id = 规范化任务内容哈希 + 预算/配置/记忆状态
        task_hash = _task_content_hash(request.task_content, cfg.hash_algo)
        state_digest = self._request_id(entries, budget)

        result = RouteResult(
            request_id=self._request_id(entries, budget, task_hash),
            budget_tokens=budget,
            total_estimated_tokens=total,
            decisions=decisions,
            config_digest=cfg.digest(),
            task_content_hash=task_hash,
            episode_id=request.episode_id,
            step_id=request.step_id,
            repo_versions=dict(request.repo_versions),
        )
        self.logger.emit(
            "route",
            request_id=result.request_id,
            episode_id=request.episode_id,
            step_id=request.step_id,
            # 任务内容只落哈希与长度，不落原文（脱敏要求）
            task_content_hash=task_hash,
            task_content_chars=(
                len(request.task_content) if request.task_content else 0
            ),
            state_digest=state_digest,
            budget_tokens=budget,
            total_estimated_tokens=total,
            config_digest=result.config_digest,
            repo_versions=dict(request.repo_versions),
            memory_snapshot={
                e.symbol_id: {"validity": e.validity, "version": e.version}
                for e in entries
            },
            request_meta=request.request_meta,
            simulated={
                "kv": cfg.simulate_kv,
                "summary": cfg.simulate_summary,
                "note": "P0 KV cache is simulated (sim:// pointers); no real "
                        "tensor is allocated or reused",
            },
            capabilities=dict(CAPABILITY_STATUS),
            decisions=[d.to_dict() for d in decisions],
        )
        return result

    def _request_id(
        self, entries: list[MemoryEntry], budget: int, task_hash: str = ""
    ) -> str:
        payload = {
            "task_content_hash": task_hash,
            "budget": budget,
            "config_digest": self.config.digest(),
            "entries": [
                {
                    "symbol_id": e.symbol_id,
                    "validity": e.validity,
                    "content_hash": e.content_hash,
                    "version": e.version,
                    "kv_ptr": e.kv_ptr,
                    "size_bytes": e.size_bytes,
                    "summary_len": len(e.summary or ""),
                }
                for e in sorted(entries, key=lambda x: x.symbol_id)
            ],
        }
        raw = _dumps(payload)
        return content_hash(raw, self.config.hash_algo)[:16]


def _dumps(obj) -> bytes:
    import json

    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _normalize_task(text: str) -> str:
    """任务内容规范化：NFKC + 空白折叠 + 去首尾（仅用于哈希，不落原文）。"""
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", normalized).strip()


def _task_content_hash(task_content: str | None, algo: str) -> str:
    if task_content is None:
        payload = b""
    else:
        payload = _normalize_task(task_content).encode("utf-8")
    return content_hash(payload, algo)
