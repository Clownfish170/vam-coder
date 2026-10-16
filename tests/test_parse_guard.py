"""任务 A 回归测试：解析不完整 / 仓库根无效时禁止错误 tombstone。

覆盖：语法错误（部分解析）、文件读取失败、仓库路径不存在/不是目录、
真实删除仍要 tombstone、语言配置失效、verify 中的读取失败与部分解析。
旧实现（commit 37bf61c）下前四项均会错误地把符号 tombstone 或把
空解析当“全部删除”。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Validity
from vam_coder.store import StaticStore

from conftest import REPO_V1, sid

# 读取成功但语法完全不可解析 → tree-sitter 报错且提取不到任何符号
BROKEN_CORE = "@@@ not python (((\n"


def _manager(store, config, tmp_path) -> InvalidationManager:
    return InvalidationManager(store, config, JsonlLogger(tmp_path / "inv.jsonl"))


def _all_valid(store: StaticStore, repo_id: str = "demo") -> bool:
    return all(
        e.validity == Validity.VALID.value
        for e in store.list_symbols(repo_id).values()
    )


# ---------- 1. 语法错误 → 不推断删除 ----------
def test_syntax_error_file_never_tombstones_symbols(
    store, config, fresh_repo, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    core_ids = [
        sid("demo", "core.py", "compute"),
        sid("demo", "core.py", "helper"),
    ]
    assert _all_valid(store)

    broken = dict(REPO_V1)
    broken["core.py"] = BROKEN_CORE
    fresh_repo(broken)
    out = mgr.sync(repo, "demo")

    assert out.tombstoned == [], "解析失败的文件不得产生 tombstone"
    for cid in core_ids:
        entry = store.get(cid)
        assert entry.validity == Validity.UNVERIFIED.value, (
            "读取成功但解析不完整 → 保留并收紧为 unverified"
        )
        assert entry.version == 1, "不可确认 ≠ 内容变化，版本不 bump"
    assert {u["symbol_id"] for u in out.unconfirmed} == set(core_ids)
    assert all(
        u["reason"] == "file_partial" for u in out.unconfirmed
    ), out.unconfirmed
    assert any(
        w["path"] == "core.py" and "tree_sitter_has_error" in w["reason"]
        for w in out.parse_warnings
    )
    # 幂等：同一坏文件重复同步不再产生变化
    ver = store.get_repo_version("demo")
    out2 = mgr.sync(repo, "demo")
    assert not out2.mutated
    assert store.get_repo_version("demo") == ver
    assert store.get(core_ids[0]).validity == Validity.UNVERIFIED.value


# ---------- 2. 文件读取失败 → 不推断删除 ----------
def test_read_failure_file_never_tombstones_symbols(
    store, config, fresh_repo, tmp_path, monkeypatch
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")

    orig_read = Path.read_bytes

    def flaky_read(self: Path) -> bytes:
        if self.name == "core.py" and self.parent == repo:
            raise OSError("permission denied (injected read failure)")
        return orig_read(self)

    monkeypatch.setattr(Path, "read_bytes", flaky_read)
    try:
        out = mgr.sync(repo, "demo")
    finally:
        monkeypatch.undo()

    assert out.tombstoned == []
    for name in ("compute", "helper"):
        entry = store.get(sid("demo", "core.py", name))
        assert entry.validity == Validity.UNVERIFIED.value
        assert entry.version == 1
    reasons = {u["symbol_id"]: u["reason"] for u in out.unconfirmed}
    assert reasons.get(sid("demo", "core.py", "compute")) == "file_failed"
    assert any(
        w["path"] == "core.py" and w["reason"].startswith("read_error")
        for w in out.parse_warnings
    )
    # app.py 解析正常：不受影响
    assert store.get(sid("demo", "app.py", "lone")).validity == (
        Validity.VALID.value
    )


# ---------- 3. 仓库路径不存在 → 抛错且状态不动 ----------
def test_missing_repo_root_aborts_sync_without_touching_state(
    store, config, repo_v1: Path, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    mgr.sync(repo_v1, "demo")
    before_ver = store.get_repo_version("demo")
    before = {k: (v.version, v.validity) for k, v in
              store.list_symbols("demo").items()}

    with pytest.raises(FileNotFoundError):
        mgr.sync(tmp_path / "definitely_not_here", "demo")

    assert store.get_repo_version("demo") == before_ver, (
        "根不存在时不得 bump 版本（旧实现：空解析→全部 tombstone）"
    )
    after = {k: (v.version, v.validity) for k, v in
             store.list_symbols("demo").items()}
    assert after == before
    assert _all_valid(store)


def test_repo_root_not_a_directory_aborts_sync(
    store, config, repo_v1: Path, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    mgr.sync(repo_v1, "demo")
    not_a_dir = tmp_path / "a_file.py"
    not_a_dir.write_text("def f():\n    return 1\n", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        mgr.sync(not_a_dir, "demo")
    assert _all_valid(store)


# ---------- 4. 真实删除（与解析失败区分）仍要 tombstone ----------
def test_genuine_file_deletion_still_tombstones(
    store, config, fresh_repo, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")

    (repo / "core.py").unlink()  # 真实删除整个文件
    out = mgr.sync(repo, "demo")

    assert sid("demo", "core.py", "compute") in out.tombstoned
    assert sid("demo", "core.py", "helper") in out.tombstoned
    assert store.get(sid("demo", "core.py", "compute")).validity == (
        Validity.TOMBSTONED.value
    )
    assert out.unconfirmed == [], "真实删除不进 unconfirmed"
    # 闭包传播不受影响
    assert store.get(sid("demo", "app.py", "run")).validity == (
        Validity.UNVERIFIED.value
    )
    assert store.get(sid("demo", "app.py", "lone")).validity == (
        Validity.VALID.value
    )


# ---------- 5. 语言配置失效（unsupported）→ 不推断删除 ----------
def test_language_config_drop_does_not_tombstone(
    store, config, repo_v1: Path, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    mgr.sync(repo_v1, "demo")

    config.supported_languages = {}  # 模拟 .py 不再被支持
    out = mgr.sync(repo_v1, "demo")

    assert out.tombstoned == []
    entries = store.list_symbols("demo")
    assert len(entries) == 4
    for entry in entries.values():
        assert entry.validity == Validity.UNVERIFIED.value
        assert entry.version == 1


# ---------- 6. verify 侧：读取失败 / 部分解析 ----------
def test_verify_read_failure_does_not_tombstone(
    store, config, fresh_repo, tmp_path, monkeypatch
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    compute_id = sid("demo", "core.py", "compute")

    orig_read = Path.read_bytes

    def flaky_read(self: Path) -> bytes:
        if self.name == "core.py":
            raise OSError("injected verify read failure")
        return orig_read(self)

    monkeypatch.setattr(Path, "read_bytes", flaky_read)
    try:
        result = mgr.verify(compute_id, repo)
    finally:
        monkeypatch.undo()

    assert result == Validity.UNVERIFIED.value
    assert store.get(compute_id).validity == Validity.UNVERIFIED.value
    events = JsonlLogger.read_all(tmp_path / "inv.jsonl")
    blocked = [e for e in events if e["event"] == "verify_inconclusive"]
    assert blocked and "read_error" in blocked[-1]["reason"]
    assert "content_match" in blocked[-1]


def test_verify_partial_parse_missing_symbol_not_tombstoned(
    store, config, fresh_repo, tmp_path
):
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    compute_id = sid("demo", "core.py", "compute")

    broken = dict(REPO_V1)
    broken["core.py"] = BROKEN_CORE
    fresh_repo(broken)

    result = mgr.verify(compute_id, repo)
    assert result == Validity.UNVERIFIED.value, (
        "部分解析中未观察到符号 ≠ 符号被删除"
    )
    assert store.get(compute_id).validity == Validity.UNVERIFIED.value


def test_verify_missing_repo_root_raises(store, config, repo_v1, tmp_path):
    mgr = _manager(store, config, tmp_path)
    mgr.sync(repo_v1, "demo")
    with pytest.raises(FileNotFoundError):
        mgr.verify(sid("demo", "core.py", "compute"), tmp_path / "nope")
    assert store.get(sid("demo", "core.py", "compute")).validity == (
        Validity.VALID.value
    )
