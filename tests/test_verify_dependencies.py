"""任务 B 回归测试：verify 恢复协议的依赖门控。

核心语义：自身源码哈希与记忆依据一致只是**必要条件**；
依赖缺失 / validity≠valid / dep_edges 不一致 / 依赖集漂移 / 依赖快照
（版本+内容）不匹配 → 不得恢复 valid。依赖检查带 visited 集，
循环依赖不导致无限递归。
"""

from __future__ import annotations

from pathlib import Path

from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Validity

from conftest import REPO_V1, REPO_V2_COMPUTE_CHANGED, REPO_V2_RENAMED, sid

CYCLE_REPO = {
    "cyc.py": (
        "def a(x):\n"
        "    return b(x)\n"
        "\n"
        "\n"
        "def b(x):\n"
        "    return a(x) + 1\n"
    ),
    "main.py": (
        "def entry():\n"
        "    return a(1)\n"
    ),
}


def _manager(store, config, tmp_path) -> InvalidationManager:
    return InvalidationManager(store, config, JsonlLogger(tmp_path / "inv.jsonl"))


def _drive_to_unverified(store, config, tmp_path):
    """compute 变化 → helper 进入 unverified；返回 (mgr, repo)。"""
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    from conftest import write_repo  # 局部导入避免顶层冗余

    write_repo(repo, dict(REPO_V2_COMPUTE_CHANGED))
    out = mgr.sync(repo, "demo")
    assert sid("demo", "core.py", "helper") in out.unverified
    return mgr, repo


def _last_event(tmp_path, name: str) -> dict:
    events = JsonlLogger.read_all(tmp_path / "inv.jsonl")
    matched = [e for e in events if e["event"] == name]
    assert matched, f"missing event {name} in log"
    return matched[-1]


# ---------- 1. 依赖 stale → 自身哈希匹配也拒绝恢复 ----------
def test_verify_blocked_while_dep_stale(store, config, fresh_repo, tmp_path):
    mgr, repo = _drive_to_unverified(store, config, tmp_path)
    helper_id = sid("demo", "core.py", "helper")
    # compute 此刻是 stale（依赖失效）
    assert store.get(sid("demo", "core.py", "compute")).validity == (
        Validity.STALE.value
    )

    result = mgr.verify(helper_id, repo)
    assert result == Validity.UNVERIFIED.value, (
        "依赖 stale 时不得恢复 valid（修复前会直接升 valid）"
    )
    assert store.get(helper_id).validity == Validity.UNVERIFIED.value

    ev = _last_event(tmp_path, "verify_blocked")
    assert ev["content_match"] is True, "判断1：自身内容一致"
    assert ev["deps_ok"] is False, "判断2：依赖状态不支持"
    assert any("not trustworthy" in r for r in ev["dep_reasons"])


# ---------- 2. 依赖已恢复 → 允许恢复 valid ----------
def test_verify_allowed_after_dep_restored(
    store, config, fresh_repo, tmp_path
):
    mgr, repo = _drive_to_unverified(store, config, tmp_path)
    helper_id = sid("demo", "core.py", "helper")
    assert mgr.verify(helper_id, repo) == Validity.UNVERIFIED.value

    # 源码回退 → sync 自动把 compute revert 为 valid；helper 仍 unverified
    fresh_repo(REPO_V1)
    out = mgr.sync(repo, "demo")
    assert sid("demo", "core.py", "compute") in out.reverted
    assert store.get(helper_id).validity == Validity.UNVERIFIED.value

    assert mgr.verify(helper_id, repo) == Validity.VALID.value
    assert store.get(helper_id).validity == Validity.VALID.value
    ev = _last_event(tmp_path, "verify_confirmed")
    assert ev["content_match"] is True and ev["deps_ok"] is True


# ---------- 3. 依赖被删除（重命名 → tombstone）→ 拒绝 ----------
def test_verify_blocked_when_dep_tombstoned(
    store, config, fresh_repo, tmp_path
):
    mgr, repo = _drive_to_unverified(store, config, tmp_path)
    helper_id = sid("demo", "core.py", "helper")

    fresh_repo(REPO_V2_RENAMED)  # compute → calc：依赖消失
    out = mgr.sync(repo, "demo")
    assert sid("demo", "core.py", "compute") in out.tombstoned

    result = mgr.verify(helper_id, repo)
    assert result == Validity.UNVERIFIED.value, (
        "依赖已删除（tombstoned）时不得恢复 valid"
    )
    ev = _last_event(tmp_path, "verify_blocked")
    assert any(
        "unconfirmed" in r or "not trustworthy" in r or "missing" in r
        for r in ev["dep_reasons"]
    ), ev["dep_reasons"]


# ---------- 4. 依赖行缺失 → 拒绝 ----------
def test_verify_blocked_when_dep_row_missing(
    store, config, fresh_repo, tmp_path
):
    mgr, repo = _drive_to_unverified(store, config, tmp_path)
    helper_id = sid("demo", "core.py", "helper")
    compute_id = sid("demo", "core.py", "compute")
    # 模拟依赖记录丢失（比 tombstone 更极端：行直接不存在）
    store.conn.execute("DELETE FROM symbols WHERE symbol_id = ?", (compute_id,))
    store.commit()

    result = mgr.verify(helper_id, repo)
    assert result == Validity.UNVERIFIED.value
    ev = _last_event(tmp_path, "verify_blocked")
    assert any("missing from store" in r for r in ev["dep_reasons"])


# ---------- 5. 依赖边缺失 → 拒绝（valid 也收紧为 unverified）----------
def test_verify_blocked_when_dep_edges_missing(
    store, config, repo_v1: Path, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    mgr.sync(repo_v1, "demo")
    helper_id = sid("demo", "core.py", "helper")
    store.conn.execute(
        "DELETE FROM dep_edges WHERE depender = ?", (helper_id,)
    )
    store.commit()

    result = mgr.verify(helper_id, repo_v1)
    assert result == Validity.UNVERIFIED.value, (
        "dep_edges 与存储 deps 不一致 → 依赖关系无法确认"
    )
    assert store.get(helper_id).validity == Validity.UNVERIFIED.value
    ev = _last_event(tmp_path, "verify_blocked")
    assert any("dep_edges" in r for r in ev["dep_reasons"])


# ---------- 6. 依赖快照版本不匹配 → 当次拒绝，刷新后可恢复 ----------
def test_verify_blocked_on_dependency_snapshot_mismatch(
    store, config, fresh_repo, tmp_path
):
    mgr, repo = _drive_to_unverified(store, config, tmp_path)
    helper_id = sid("demo", "core.py", "helper")
    compute_id = sid("demo", "core.py", "compute")

    # 依赖回到 valid 但版本已被推进（快照记录的是传播时刻的版本）
    fresh_repo(REPO_V1)
    mgr.sync(repo, "demo")
    assert store.get(compute_id).validity == Validity.VALID.value
    store.conn.execute(
        "UPDATE symbols SET version = version + 1 WHERE symbol_id = ?",
        (compute_id,),
    )
    store.commit()

    result = mgr.verify(helper_id, repo)
    assert result == Validity.UNVERIFIED.value, (
        "依赖版本与快照不匹配 → 本次不得恢复 valid"
    )
    ev = _last_event(tmp_path, "verify_blocked")
    assert any("snapshot mismatch" in r for r in ev["dep_reasons"])
    # 快照已刷新：依赖状态未再变化时，再次显式 verify 可恢复
    assert mgr.verify(helper_id, repo) == Validity.VALID.value


# ---------- 7. 循环依赖：终止且语义正确（无无限递归）----------
def test_circular_dependency_verify_terminates(
    store, config, fresh_repo, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    fresh_repo(dict(CYCLE_REPO))  # 清空目录后写入循环依赖仓库
    mgr.sync(repo, "demo")
    a_id = sid("demo", "cyc.py", "a")
    b_id = sid("demo", "cyc.py", "b")

    # b 变化 → a unverified（经依赖边 b←a）
    changed = dict(CYCLE_REPO)
    changed["cyc.py"] = CYCLE_REPO["cyc.py"].replace(
        "return a(x) + 1", "return a(x) + 2"
    )
    fresh_repo(changed)
    out = mgr.sync(repo, "demo")
    assert sid("demo", "cyc.py", "b") in out.content_changed
    assert a_id in out.unverified

    # 依赖 b 仍 stale → 拒绝（BFS 终止，无 RecursionError）
    assert mgr.verify(a_id, repo) == Validity.UNVERIFIED.value

    # b 回退 → valid 后 a 可恢复
    fresh_repo(dict(CYCLE_REPO))
    mgr.sync(repo, "demo")
    assert store.get(b_id).validity == Validity.VALID.value
    assert mgr.verify(a_id, repo) == Validity.VALID.value


# ---------- 8. 日志：两种判断字段齐备 ----------
def test_verify_log_distinguishes_content_and_dependency_checks(
    store, config, fresh_repo, tmp_path
):
    mgr, repo = _drive_to_unverified(store, config, tmp_path)
    helper_id = sid("demo", "core.py", "helper")
    mgr.verify(helper_id, repo)  # blocked（依赖 stale）
    events = JsonlLogger.read_all(tmp_path / "inv.jsonl")
    blocked = [e for e in events if e["event"] == "verify_blocked"]
    assert blocked
    ev = blocked[-1]
    assert ev["content_match"] is True
    assert ev["deps_ok"] is False
    assert "necessary condition" in ev["reason"]
    assert "sufficient condition" in ev["reason"]
