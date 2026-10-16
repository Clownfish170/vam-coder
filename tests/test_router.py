"""路由器测试 —— 对应必过测试 5、6，另覆盖预算降级路径。"""

from __future__ import annotations

import pytest

from vam_coder.logging_util import JsonlLogger
from vam_coder.models import (
    Action,
    MemoryEntry,
    RouteRequest,
    Validity,
)
from vam_coder.router import RuleRouter


def make_entry(
    symbol_id: str,
    validity: str = Validity.VALID.value,
    *,
    with_kv: bool = True,
    summary: str = "short summary of symbol",
    size_bytes: int = 400,
    deps: list[str] | None = None,
) -> MemoryEntry:
    return MemoryEntry(
        symbol_id=symbol_id,
        repo_id="demo",
        file_path="core.py",
        qualified_name=symbol_id.split("::")[-1],
        kind="function",
        content_hash="h" * 64,
        source_hash="h" * 64,
        version=1,
        deps=deps or [],
        summary=summary,
        validity=validity,
        kv_ptr="sim://kv/py-model/0123456789abcdef" if with_kv else None,
        provenance={"task_id": "t", "outcome": "indexed"},
        size_bytes=size_bytes,
        start_line=1,
        end_line=10,
        last_seen_repo_version=1,
        updated_at="2026-10-16T00:00:00+00:00",
    )


# ---------- 必过测试 5：失效记忆不能执行 REUSE_KV ----------
@pytest.mark.parametrize(
    "validity,expected",
    [
        (Validity.STALE.value, Action.EXPAND.value),
        (Validity.UNVERIFIED.value, Action.EXPAND.value),
        (Validity.TOMBSTONED.value, Action.DROP.value),
    ],
)
def test_invalid_memories_never_reuse_kv(config, validity, expected):
    entries = [
        make_entry("demo:core.py::bad", validity),
        make_entry("demo:core.py::good", Validity.VALID.value),
    ]
    router = RuleRouter(config, JsonlLogger(None))
    result = router.route(RouteRequest(entries=entries))
    actions = result.actions()
    assert actions["demo:core.py::bad"] == expected
    assert actions["demo:core.py::bad"] != Action.REUSE_KV.value
    # 对照：valid 条目正常走 REUSE_KV（证明门控确实由 validity 驱动）
    assert actions["demo:core.py::good"] == Action.REUSE_KV.value

    bad = next(d for d in result.decisions if d.symbol_id.endswith("::bad"))
    assert any("REUSE_KV forbidden" in r or "not a valid object" in r
               for r in bad.reasons), "日志理由必须解释为何禁止 REUSE_KV"


def test_tombstoned_is_not_a_valid_object(config):
    router = RuleRouter(config, JsonlLogger(None))
    result = router.route(
        RouteRequest(entries=[make_entry(
            "demo:core.py::gone", Validity.TOMBSTONED.value
        )])
    )
    decision = result.decisions[0]
    assert decision.action == Action.DROP.value
    assert decision.validity == Validity.TOMBSTONED.value
    assert decision.est_tokens == 0


# ---------- 必过测试 6：相同输入可复现 + 日志解释路由决策 ----------
def test_routing_reproducible_and_logged(config, tmp_path):
    log_path = tmp_path / "decisions.jsonl"
    entries = [
        make_entry("demo:core.py::a", Validity.VALID.value),
        make_entry("demo:core.py::b", Validity.STALE.value),
        make_entry("demo:core.py::c", Validity.UNVERIFIED.value),
        make_entry("demo:core.py::d", Validity.TOMBSTONED.value),
        make_entry("demo:core.py::e", Validity.VALID.value, with_kv=False),
    ]

    r1 = RuleRouter(config, JsonlLogger(log_path)).route(
        RouteRequest(entries=entries, request_meta={"step": 1})
    )
    # 打乱输入顺序再跑：结果必须只由内容决定
    shuffled = list(reversed(entries))
    r2 = RuleRouter(config, JsonlLogger(log_path)).route(
        RouteRequest(entries=shuffled, request_meta={"step": 2})
    )

    assert r1.request_id == r2.request_id, "相同输入 → 相同 request_id"
    assert r1.actions() == r2.actions(), "相同输入 → 相同动作分配"
    assert r1.total_estimated_tokens == r2.total_estimated_tokens

    events = JsonlLogger.read_all(log_path)
    route_events = [e for e in events if e["event"] == "route"]
    assert len(route_events) == 2
    for ev in route_events:
        assert ev["simulated"]["kv"] is True, "日志必须声明 KV 为模拟功能"
        for d in ev["decisions"]:
            assert d["reasons"], f"决策 {d['symbol_id']} 缺少解释理由"
            joined = " | ".join(d["reasons"])
            # 理由必须能对应到该决策的依据
            assert any(
                key in joined
                for key in (
                    "validity=", "budget", "kv_ptr", "default", "final action"
                )
            ), joined

    # 具体条目理由可解释性抽查
    ev = route_events[-1]
    by_id = {d["symbol_id"]: d for d in ev["decisions"]}
    assert any("stale" in r for r in by_id["demo:core.py::b"]["reasons"])
    assert any("unverified" in r for r in by_id["demo:core.py::c"]["reasons"])
    assert any("tombstoned" in r
               for r in by_id["demo:core.py::d"]["reasons"])
    assert any("kv_ptr available" in r
               for r in by_id["demo:core.py::a"]["reasons"])
    assert any("kv_ptr missing" in r
               for r in by_id["demo:core.py::e"]["reasons"])


# ---------- 预算降级路径（全局规则） ----------
def test_budget_forces_downgrade(config, tmp_path):
    entries = [
        make_entry("demo:core.py::big", size_bytes=4000),
        make_entry("demo:core.py::small", size_bytes=100),
        make_entry("demo:core.py::stale_big",
                   Validity.STALE.value, size_bytes=4000),
    ]
    log_path = tmp_path / "decisions.jsonl"
    router = RuleRouter(config, JsonlLogger(log_path))
    # 预算紧张：stale（keep-score 最低、代价最高）先被丢弃
    result = router.route(RouteRequest(entries=entries, budget_tokens=130))
    actions = result.actions()
    assert actions["demo:core.py::stale_big"] == Action.DROP.value
    assert result.total_estimated_tokens <= 130
    # 超预算过程写进了理由
    ev = [e for e in JsonlLogger.read_all(log_path)
          if e["event"] == "route"][-1]
    dropped = next(d for d in ev["decisions"]
                   if d["symbol_id"] == "demo:core.py::stale_big")
    assert any("budget over" in r for r in dropped["reasons"])


def test_budget_allows_compress_for_valid(config):
    entries = [
        make_entry("demo:core.py::a", size_bytes=4000, summary="brief note"),
    ]
    router = RuleRouter(config, JsonlLogger(None))
    # 预算介于摘要代价(2)与 KV 复用代价(32)之间 → 降级为 COMPRESS
    result = router.route(RouteRequest(entries=entries, budget_tokens=20))
    assert result.actions()["demo:core.py::a"] == Action.COMPRESS.value
    assert result.total_estimated_tokens <= 20
