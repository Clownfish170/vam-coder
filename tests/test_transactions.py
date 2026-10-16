"""任务 D 回归测试：一次 sync/verify 的事务一致性与日志审计策略。

- 异常注入 → 版本号、符号状态、依赖边全部回滚（旧实现：版本号已
  bump 提交、符号只更新一半）；
- 嵌套 commit 不得提交外层事务；
- JSONL 无法回滚 → 事务内事件只入缓冲，提交后落盘；回滚时丢弃并
  单独追加 sync_aborted / verify_aborted（可审计，不假称原子一致）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import MemoryEntry, Validity
from vam_coder.store import StaticStore

from conftest import REPO_V2_COMPUTE_CHANGED, sid


def _manager(store, config, tmp_path) -> InvalidationManager:
    return InvalidationManager(store, config, JsonlLogger(tmp_path / "inv.jsonl"))


def _snapshot(store: StaticStore, repo_id: str) -> dict:
    """DB 状态全量快照：版本、符号、依赖边。"""
    symbols = {
        k: (v.version, v.content_hash, v.source_hash, v.validity,
            tuple(v.deps), v.summary, v.kv_ptr)
        for k, v in store.list_symbols(repo_id).items()
    }
    edges = sorted(
        (r["depender"], r["dependee"])
        for r in store.conn.execute(
            "SELECT depender, dependee FROM dep_edges"
        ).fetchall()
    )
    return {
        "repo_version": store.get_repo_version(repo_id),
        "symbols": symbols,
        "edges": edges,
    }


# ---------- 1. sync 中途异常 → 全量回滚 + 缓冲日志不落盘 ----------
def test_sync_failure_rolls_back_everything(
    store, config, fresh_repo, tmp_path, monkeypatch
):
    log_path = tmp_path / "inv.jsonl"
    mgr = InvalidationManager(store, config, JsonlLogger(log_path))
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    before = _snapshot(store, "demo")
    events_before = len(JsonlLogger.read_all(log_path))

    # compute 变化（写库+日志已入缓冲）→ 闭包传播写 provenance 时炸
    fresh_repo(REPO_V2_COMPUTE_CHANGED)

    def boom(*args, **kwargs):  # 实例属性替换：接收调用点原样参数
        raise RuntimeError("injected failure during dep snapshot write")

    monkeypatch.setattr(store, "set_provenance", boom)
    try:
        with pytest.raises(RuntimeError, match="injected failure"):
            mgr.sync(repo, "demo")
    finally:
        monkeypatch.undo()

    after = _snapshot(store, "demo")
    assert after == before, (
        f"回滚后必须与同步前一致：\nbefore={before}\nafter={after}"
    )
    assert store.get(sid("demo", "core.py", "compute")).validity == (
        Validity.VALID.value
    ), "stale 写入被回滚，compute 仍为 valid"

    # 日志审计：新事件仅一条 sync_aborted；半截 content_stale 不落盘
    new_events = JsonlLogger.read_all(log_path)[events_before:]
    kinds = [e["event"] for e in new_events]
    assert kinds == ["sync_aborted"], kinds
    assert "injected failure" in new_events[0]["error"]
    assert "not atomic" in new_events[0]["note"]

    # 故障排除后重新同步可正常推进（回滚不是死锁）
    out = mgr.sync(repo, "demo")
    assert sid("demo", "core.py", "compute") in out.content_changed
    assert store.get_repo_version("demo") == before["repo_version"] + 1


# ---------- 2. 嵌套函数里的 commit 不得提交外层事务 ----------
def test_inner_commit_does_not_escape_outer_transaction(store: StaticStore):
    def _entry(symbol_id: str) -> MemoryEntry:
        return MemoryEntry(
            symbol_id=symbol_id, repo_id="demo", file_path="core.py",
            qualified_name=symbol_id.split("::")[-1], kind="function",
            content_hash="a" * 64, source_hash="a" * 64, version=1,
            deps=[], summary="s", validity=Validity.VALID.value,
            kv_ptr=None, provenance=None, size_bytes=10,
            start_line=1, end_line=2, last_seen_repo_version=1,
            updated_at="2026-10-16T00:00:00+00:00",
        )

    with pytest.raises(RuntimeError, match="outer failure"):
        with store.transaction():
            store.insert_symbol(_entry("demo:core.py::f"))
            store.commit()  # 事务内应为 no-op（所有权在最外层）
            raise RuntimeError("outer failure")

    assert store.get("demo:core.py::f") is None, (
        "内层 commit 意外提交了外层事务"
    )

    # 正常提交路径仍持久化
    with store.transaction():
        store.insert_symbol(_entry("demo:core.py::f"))
        store.commit()
    assert store.get("demo:core.py::f") is not None


# ---------- 3. verify 中途异常 → 回滚 + verify_aborted ----------
def test_verify_failure_rolls_back(
    store, config, fresh_repo, tmp_path, monkeypatch
):
    log_path = tmp_path / "inv.jsonl"
    mgr = InvalidationManager(store, config, JsonlLogger(log_path))
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    fresh_repo(REPO_V2_COMPUTE_CHANGED)
    mgr.sync(repo, "demo")
    compute_id = sid("demo", "core.py", "compute")
    entry_before = store.get(compute_id)
    assert entry_before.validity == Validity.STALE.value
    events_before = len(JsonlLogger.read_all(log_path))

    def boom(self, *args, **kwargs):
        raise RuntimeError("injected failure in apply_source_change")

    monkeypatch.setattr(store, "apply_source_change", boom)
    try:
        with pytest.raises(RuntimeError, match="injected failure"):
            mgr.verify(compute_id, repo)
    finally:
        monkeypatch.undo()

    entry_after = store.get(compute_id)
    assert entry_after.version == entry_before.version, "版本回滚"
    assert entry_after.source_hash == entry_before.source_hash, "哈希回滚"
    assert entry_after.validity == Validity.STALE.value, "状态回滚"

    new_events = JsonlLogger.read_all(log_path)[events_before:]
    kinds = [e["event"] for e in new_events]
    assert kinds == ["verify_aborted"], kinds


# ---------- 4. 读侧不受失败同步影响（无悬挂事务、可继续推进）----------
def test_reads_stable_and_sync_recovers_after_failed_sync(
    store, config, fresh_repo, tmp_path, monkeypatch
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    snap1 = _snapshot(store, "demo")

    fresh_repo(REPO_V2_COMPUTE_CHANGED)  # 下次 sync 有写入 → 会调 bump

    def boom(*args, **kwargs):
        raise RuntimeError("injected")

    monkeypatch.setattr(store, "bump_repo_version", boom)
    try:
        with pytest.raises(RuntimeError):
            mgr.sync(repo, "demo")
    finally:
        monkeypatch.undo()

    # 失败后无悬挂事务：读取稳定，与失败前一致
    assert _snapshot(store, "demo") == snap1
    # 故障排除后同步可正常推进
    out = mgr.sync(repo, "demo")
    assert out.content_changed == [sid("demo", "core.py", "compute")]
    assert store.get_repo_version("demo") == snap1["repo_version"] + 1
