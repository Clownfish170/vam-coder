"""任务 G：能力边界标注（implemented / simulated / not_implemented）。

- 路由器只输出动作决策；EXPAND ≠ 已执行源码读取/装配/推理/ KV 复用；
- CAPABILITY_STATUS 与决策日志中的 capabilities 字段必须一致。
"""

from __future__ import annotations

from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Action, MemoryEntry, RouteRequest, Validity
from vam_coder.router import CAPABILITY_STATUS, RuleRouter


def _entry(symbol_id: str, validity: str, *, kv: bool = True) -> MemoryEntry:
    return MemoryEntry(
        symbol_id=symbol_id,
        repo_id="demo",
        file_path="core.py",
        qualified_name=symbol_id.split("::")[-1],
        kind="function",
        content_hash="h" * 64,
        source_hash="h" * 64,
        version=1,
        deps=[],
        summary="summary text",
        validity=validity,
        kv_ptr="sim://kv/py-model/0123456789abcdef" if kv else None,
        provenance=None,
        size_bytes=400,
        start_line=1,
        end_line=10,
        last_seen_repo_version=1,
        updated_at="2026-10-16T00:00:00+00:00",
    )


ALLOWED = {"implemented", "simulated", "not_implemented"}


def test_capability_status_labels_are_complete():
    assert set(CAPABILITY_STATUS.values()) <= ALLOWED
    # 模拟能力
    assert CAPABILITY_STATUS["kv_cache_reuse"] == "simulated"
    assert CAPABILITY_STATUS["summary_generation"] == "simulated"
    assert CAPABILITY_STATUS["token_estimation"] == "simulated"
    # 未实现能力（不得声称已做）
    assert CAPABILITY_STATUS["expand_source_read_and_assembly"] == \
        "not_implemented"
    assert CAPABILITY_STATUS["model_inference"] == "not_implemented"
    assert CAPABILITY_STATUS["model_summary_generation"] == \
        "not_implemented"
    # 已实现能力
    for key in ("symbol_index", "content_hash_versioning",
                "dependency_invalidation_closure", "tombstone",
                "rule_routing_decision", "request_decision_logging"):
        assert CAPABILITY_STATUS[key] == "implemented", key


def test_route_log_declares_capabilities(config, tmp_path):
    log_path = tmp_path / "d.jsonl"
    router = RuleRouter(config, JsonlLogger(log_path))
    router.route(
        RouteRequest(entries=[
            _entry("demo:core.py::stale_one", Validity.STALE.value),
            _entry("demo:core.py::tomb_one", Validity.TOMBSTONED.value),
            _entry("demo:core.py::bad_kv", Validity.VALID.value, kv=False),
        ])
    )
    ev = [e for e in JsonlLogger.read_all(log_path)
          if e["event"] == "route"][-1]
    assert ev["capabilities"] == CAPABILITY_STATUS
    assert ev["simulated"]["kv"] is True


def test_expand_is_decision_only_in_reasons(config, tmp_path):
    log_path = tmp_path / "d.jsonl"
    router = RuleRouter(config, JsonlLogger(log_path))
    result = router.route(RouteRequest(entries=[
        _entry("demo:core.py::stale_one", Validity.STALE.value),
        _entry("demo:core.py::no_kv", Validity.VALID.value, kv=False),
    ]))
    assert result.actions()["demo:core.py::stale_one"] == Action.EXPAND.value
    assert result.actions()["demo:core.py::no_kv"] == Action.EXPAND.value

    ev = [e for e in JsonlLogger.read_all(log_path)
          if e["event"] == "route"][-1]
    for d in ev["decisions"]:
        assert d["action"] == Action.EXPAND.value
        joined = " | ".join(d["reasons"])
        assert "routing decision only" in joined, (
            "EXPAND 必须显式声明为仅决策、未执行读取/装配/推理"
        )
        assert "not implemented" in joined
