"""失效管理测试 —— 对应必过测试 1–4。"""

from __future__ import annotations

from pathlib import Path

from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Validity
from vam_coder.store import StaticStore

from conftest import (
    REPO_V1,
    REPO_V2_COMPUTE_CHANGED,
    REPO_V2_LONE_DELETED,
    REPO_V2_RENAMED,
    sid,
)


def _manager(store, config, tmp_path) -> InvalidationManager:
    return InvalidationManager(store, config, JsonlLogger(tmp_path / "inv.jsonl"))


def _snapshot(store: StaticStore, repo_id: str) -> dict:
    return {
        k: (v.version, v.content_hash, v.source_hash, v.validity,
            tuple(v.deps), v.summary, v.kv_ptr)
        for k, v in store.list_symbols(repo_id).items()
    }


# ---------- 必过测试 1：源码未变化 → 哈希与版本状态保持一致 ----------
def test_unchanged_source_keeps_hash_and_version(
    store, config, repo_v1: Path, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    out1 = mgr.sync(repo_v1, "demo")
    assert set(out1.inserted) == {
        sid("demo", "core.py", "compute"),
        sid("demo", "core.py", "helper"),
        sid("demo", "app.py", "run"),
        sid("demo", "app.py", "lone"),
    }
    snap1 = _snapshot(store, "demo")
    ver1 = store.get_repo_version("demo")

    out2 = mgr.sync(repo_v1, "demo")
    assert not out2.mutated
    assert out2.unchanged_count == 4
    assert out2.repo_version_before == out2.repo_version_after == ver1

    snap2 = _snapshot(store, "demo")
    assert snap1 == snap2, "源码未变化时哈希/版本/validity 不得漂移"
    for entry in store.list_symbols("demo").values():
        assert entry.content_hash and entry.source_hash
        assert entry.version == 1
        assert isinstance(entry.deps, list)
        assert entry.summary
        assert entry.validity == Validity.VALID.value


# ---------- 必过测试 2：函数内容变化 → 旧记忆失效 ----------
def test_content_change_invalidates_old_memory(
    store, config, fresh_repo, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    before = store.get(sid("demo", "core.py", "compute"))
    assert before.validity == Validity.VALID.value

    fresh_repo(REPO_V2_COMPUTE_CHANGED)
    out = mgr.sync(repo, "demo")

    assert sid("demo", "core.py", "compute") in out.content_changed
    after = store.get(sid("demo", "core.py", "compute"))
    assert after.validity == Validity.STALE.value, "内容变化必须使旧记忆失效"
    assert after.version == 2, "内容变化必须 bump 符号版本"
    assert after.content_hash == before.content_hash, (
        "content_hash 是记忆依据，不应被当前源码覆盖"
    )
    assert after.source_hash != before.source_hash
    assert out.repo_version_after == out.repo_version_before + 1


# ---------- 必过测试 3：依赖函数变化 → 依赖方按规则进入 unverified ----------
def test_dependency_change_marks_dependents_unverified(
    store, config, fresh_repo, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")

    fresh_repo(REPO_V2_COMPUTE_CHANGED)
    out = mgr.sync(repo, "demo")

    assert store.get(sid("demo", "core.py", "compute")).validity == \
        Validity.STALE.value
    # d=1：helper 直接调用 compute
    assert sid("demo", "core.py", "helper") in out.unverified
    assert store.get(sid("demo", "core.py", "helper")).validity == \
        Validity.UNVERIFIED.value
    # d=2：run 调用 helper（闭包深度上限 2 之内）
    assert sid("demo", "app.py", "run") in out.unverified
    assert store.get(sid("demo", "app.py", "run")).validity == \
        Validity.UNVERIFIED.value
    # 无关符号保持 valid
    assert store.get(sid("demo", "app.py", "lone")).validity == \
        Validity.VALID.value
    # 依赖方自身内容没变：版本不 bump，content_hash 不变
    helper = store.get(sid("demo", "core.py", "helper"))
    assert helper.version == 1
    assert helper.content_hash == helper.source_hash

    # 恢复协议（任务 B）：自身哈希匹配只是必要条件——依赖 compute 仍 stale
    # 时 verify 不得恢复 valid（修复前此处直接升 valid，正是 P0 缺陷）
    assert mgr.verify(sid("demo", "core.py", "helper"), repo) == \
        Validity.UNVERIFIED.value
    assert store.get(sid("demo", "core.py", "helper")).validity == \
        Validity.UNVERIFIED.value
    # stale 条目重哈希失配 → 保持/确认 stale
    assert mgr.verify(sid("demo", "core.py", "compute"), repo) == \
        Validity.STALE.value
    # 依赖恢复（源码回退 → sync 自动 revert compute 为 valid）后，
    # 显式 verify 才允许 helper 升回 valid；sync 本身不自动治愈
    fresh_repo(REPO_V1)
    out2 = mgr.sync(repo, "demo")
    assert sid("demo", "core.py", "compute") in out2.reverted
    assert store.get(sid("demo", "core.py", "compute")).validity == \
        Validity.VALID.value
    assert store.get(sid("demo", "core.py", "helper")).validity == \
        Validity.UNVERIFIED.value
    assert mgr.verify(sid("demo", "core.py", "helper"), repo) == \
        Validity.VALID.value


# ---------- 必过测试 4：删除/重命名 → 旧符号不能被当作有效对象 ----------
def test_deleted_symbol_tombstoned(store, config, fresh_repo, tmp_path):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")

    fresh_repo(REPO_V2_LONE_DELETED)
    out = mgr.sync(repo, "demo")

    old_id = sid("demo", "app.py", "lone")
    assert old_id in out.tombstoned
    entry = store.get(old_id)
    assert entry is not None, "tombstone 保留行以便审计，但不再是有效对象"
    assert entry.validity == Validity.TOMBSTONED.value
    assert entry.validity != Validity.VALID.value
    # 默认检索接口可过滤 tombstoned
    assert old_id not in store.list_symbols("demo", include_tombstoned=False)


def test_renamed_symbol_tombstoned_and_new_inserted(
    store, config, fresh_repo, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")

    fresh_repo(REPO_V2_RENAMED)
    out = mgr.sync(repo, "demo")

    old_id = sid("demo", "core.py", "compute")
    new_id = sid("demo", "core.py", "calc")
    assert old_id in out.tombstoned
    assert new_id in out.inserted
    assert store.get(old_id).validity == Validity.TOMBSTONED.value
    assert store.get(new_id).validity == Validity.VALID.value
    assert store.get(new_id).version == 1
    # 仍调用旧名字的 helper 被闭包传播（经 tombstone 种子）
    assert store.get(sid("demo", "core.py", "helper")).validity == \
        Validity.UNVERIFIED.value
