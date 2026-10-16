"""集成测试：真实文件 → 索引 → 失效 → 路由的端到端链路（必过测试 6 的全链路版）。"""

from __future__ import annotations

from pathlib import Path

from vam_coder.config import AppConfig
from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Action, Validity
from vam_coder.pipeline import route_repo, sync_repo
from vam_coder.store import StaticStore

from conftest import (
    REPO_V2_COMPUTE_CHANGED,
    REPO_V2_LONE_DELETED,
    sid,
)


def test_end_to_end_index_invalidate_route(
    store: StaticStore, config: AppConfig, fresh_repo, tmp_path: Path
):
    decision_log = tmp_path / "decisions.jsonl"
    invalid_log = tmp_path / "invalidation.jsonl"
    dlog = JsonlLogger(decision_log)
    ilog = JsonlLogger(invalid_log)
    repo = tmp_path / "repo"

    # 1) 首次索引 + 路由：全部 valid → 全部 REUSE_KV
    out1 = sync_repo(store, repo, "demo", config, ilog)
    assert len(out1.inserted) == 4
    r1 = route_repo(store, "demo", config, logger=dlog,
                    request_meta={"step": "initial"})
    assert r1.actions() == {
        sid("demo", "core.py", "compute"): Action.REUSE_KV.value,
        sid("demo", "core.py", "helper"): Action.REUSE_KV.value,
        sid("demo", "app.py", "run"): Action.REUSE_KV.value,
        sid("demo", "app.py", "lone"): Action.REUSE_KV.value,
    }

    # 2) 修改 compute → 失效传播 + 重新路由
    fresh_repo(REPO_V2_COMPUTE_CHANGED)
    out2 = sync_repo(store, repo, "demo", config, ilog)
    assert out2.content_changed == [sid("demo", "core.py", "compute")]
    assert set(out2.unverified) == {
        sid("demo", "core.py", "helper"), sid("demo", "app.py", "run"),
    }
    r2 = route_repo(store, "demo", config, logger=dlog,
                    request_meta={"step": "after-change"})
    a2 = r2.actions()
    assert a2[sid("demo", "core.py", "compute")] == Action.EXPAND.value
    assert a2[sid("demo", "core.py", "helper")] == Action.EXPAND.value
    assert a2[sid("demo", "app.py", "run")] == Action.EXPAND.value
    assert a2[sid("demo", "app.py", "lone")] == Action.REUSE_KV.value
    assert Action.REUSE_KV.value not in (
        a2[sid("demo", "core.py", "compute")],
        a2[sid("demo", "core.py", "helper")],
        a2[sid("demo", "app.py", "run")],
    )

    # 3) 删除 lone → tombstone 路由为 DROP
    fresh_repo(REPO_V2_LONE_DELETED)
    out3 = sync_repo(store, repo, "demo", config, ilog)
    assert out3.tombstoned == [sid("demo", "app.py", "lone")]
    r3 = route_repo(store, "demo", config, logger=dlog,
                    request_meta={"step": "after-delete"})
    assert r3.actions()[sid("demo", "app.py", "lone")] == Action.DROP.value

    # 4) 仓库内容回到 v2 变更态：动作分配与第 2 步一致；
    #    同一状态下连续两次路由 → request_id / 动作完全可复现
    fresh_repo(REPO_V2_COMPUTE_CHANGED)
    sync_repo(store, repo, "demo", config, ilog)
    r2_again = route_repo(store, "demo", config, logger=dlog,
                          request_meta={"step": "after-change-repeat"})
    r2_again_b = route_repo(store, "demo", config, logger=dlog,
                            request_meta={"step": "after-change-repeat-2"})
    assert r2_again.actions() == r2.actions()
    assert r2_again.total_estimated_tokens == r2.total_estimated_tokens
    assert r2_again.request_id == r2_again_b.request_id
    assert r2_again.actions() == r2_again_b.actions()

    # 5) 日志齐备：失效事件 + 路由决策均落盘且可解释
    inv_events = JsonlLogger.read_all(invalid_log)
    kinds = {e["event"] for e in inv_events}
    assert {"insert", "content_stale", "dependent_unverified", "tombstone",
            "sync_completed"} <= kinds
    stale_ev = next(e for e in inv_events if e["event"] == "content_stale")
    assert "stale" in stale_ev["reason"]
    unver_ev = next(e for e in inv_events
                    if e["event"] == "dependent_unverified")
    assert "closure depth" in unver_ev["reason"]

    route_events = [e for e in JsonlLogger.read_all(decision_log)
                    if e["event"] == "route"]
    assert len(route_events) >= 4
    for ev in route_events:
        for d in ev["decisions"]:
            assert d["reasons"]
    # 第 2 步的重复路由（同状态两次）request_id 一致（可复现）
    ids = [ev["request_id"] for ev in route_events
           if ev["request_meta"].get("step") in ("after-change-repeat",
                                                 "after-change-repeat-2")]
    assert len(ids) == 2 and ids[0] == ids[1]
    # 模拟功能在日志中显式声明
    assert route_events[0]["simulated"]["kv"] is True
    assert route_events[0]["simulated"]["summary"] is True


def test_repeated_sync_and_route_reproducible(
    store: StaticStore, config: AppConfig, repo_v1: Path, tmp_path: Path
):
    dlog = JsonlLogger(tmp_path / "d.jsonl")
    ilog = JsonlLogger(tmp_path / "i.jsonl")
    sync_repo(store, repo_v1, "demo", config, ilog)
    sync_repo(store, repo_v1, "demo", config, ilog)  # 幂等
    r1 = route_repo(store, "demo", config, logger=dlog)
    r2 = route_repo(store, "demo", config, logger=dlog)
    assert r1.request_id == r2.request_id
    assert r1.actions() == r2.actions()
    # 未变更二次 sync 不产生失效事件
    inv = [e for e in JsonlLogger.read_all(tmp_path / "i.jsonl")
           if e["event"] in ("content_stale", "tombstone",
                             "dependent_unverified")]
    assert inv == []
