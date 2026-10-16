"""P0.3 任务 1 回归测试：不完整解析符号不得成为正式依赖目标。

场景（任务书）：broken.py 语法错误但部分 AST 提取到 helper()；
app.py 完整解析且 run() 调用 helper() —— run 不得建立指向
broken.py 未注册 helper 的依赖边（应 unresolved + detail）。
配套：完整解析文件的可信 helper 仍可建边；恢复完整解析后下一次
同步正常建边；dep_edges/symbols.deps 无指向不存在符号的边；
历史遗留悬空边可被剪除，verify 对缺失依赖安全拒绝。
"""

from __future__ import annotations

from pathlib import Path

from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Validity
from vam_coder.parser import parse_repo
from vam_coder.store import StaticStore

from conftest import sid

# broken.py：helper 可被部分提取，文件整体 has_error → partial
BROKEN_WITH_HELPER = (
    "def helper():\n"
    "    return 1\n"
    "\n"
    "def broken(:\n"
)
# 仅含 helper 的部分解析变体（单符号模块，供 import 绑定场景）
BROKEN_HELPER_ONLY = (
    "def helper():\n"
    "    return 1\n"
    "\n"
    "x = (\n"
)
# 恢复后的合法文件（内容不变）
FIXED_HELPER = (
    "def helper():\n"
    "    return 1\n"
)
APP_RUN = "def run():\n    return helper()\n"


def _write(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8")
    return root


def _manager(store, config, tmp_path) -> InvalidationManager:
    return InvalidationManager(store, config, JsonlLogger(tmp_path / "inv.jsonl"))


def _dangling_edge_count(store: StaticStore) -> int:
    """dep_edges 中指向 symbols 不存在行的边数。"""
    rows = store.conn.execute(
        "SELECT depender, dependee FROM dep_edges"
    ).fetchall()
    n = 0
    for r in rows:
        for col in ("depender", "dependee"):
            hit = store.conn.execute(
                "SELECT 1 FROM symbols WHERE symbol_id = ?", (r[col],)
            ).fetchone()
            if hit is None:
                n += 1
    return n


def _dangling_deps_count(store: StaticStore) -> int:
    """symbols.deps 中指向不存在符号的条目数。"""
    import json

    n = 0
    for row in store.conn.execute("SELECT symbol_id, deps FROM symbols"):
        for dep in json.loads(row["deps"]):
            hit = store.conn.execute(
                "SELECT 1 FROM symbols WHERE symbol_id = ?", (dep,)
            ).fetchone()
            if hit is None:
                n += 1
    return n


# ---------- 1. partial 符号不作正式目标（任务书场景）----------
def test_partial_symbol_not_used_as_dependency_target(
    tmp_path: Path, config, store
):
    root = _write(tmp_path / "repo", {
        "broken.py": BROKEN_WITH_HELPER,
        "app.py": APP_RUN,
    })
    # 解析层：部分符号仍可作为诊断观察到……
    result = parse_repo(root, "demo", config)
    diag_ids = {d.symbol_id for d in result.symbols}
    assert sid("demo", "broken.py", "helper") in diag_ids, "诊断输出保留"
    run_draft = next(
        d for d in result.symbols if d.symbol_id == sid("demo", "app.py", "run")
    )
    # ……但不得成为可信目标：run 不建边，记 unresolved
    assert run_draft.deps == [], (
        f"partial 符号被解析成依赖目标：{run_draft.deps}"
    )
    unresolved = [
        u for u in result.unresolved_calls
        if u["symbol_id"] == sid("demo", "app.py", "run")
    ]
    assert unresolved and unresolved[0]["call"] == "helper"
    assert unresolved[0]["reason"] in ("unknown_name", "ambiguous_name")
    assert unresolved[0].get("detail")

    # 存储层：同步后同样不出现坏边
    mgr = _manager(store, config, tmp_path)
    mgr.sync(root, "demo")
    run = store.get(sid("demo", "app.py", "run"))
    assert run.deps == []
    assert store.get(sid("demo", "broken.py", "helper")) is None, (
        "partial 新符号不注册（既有规则）"
    )
    assert store.direct_dependents(sid("demo", "broken.py", "helper")) == []
    assert _dangling_edge_count(store) == 0
    assert _dangling_deps_count(store) == 0


# ---------- 2. import 绑定也不得解析到 partial 符号 ----------
def test_import_binding_resolves_to_success_target_only(
    tmp_path: Path, config, store
):
    root = _write(tmp_path / "repo", {
        "broken.py": BROKEN_HELPER_ONLY,
        "app.py": "from broken import helper\n\n\ndef run():\n    return helper()\n",
    })
    result = parse_repo(root, "demo", config)
    assert result.file_status["broken.py"] == "partial"
    run_draft = next(
        d for d in result.symbols if d.symbol_id == sid("demo", "app.py", "run")
    )
    assert run_draft.deps == [], (
        f"import 绑定解析到了 partial 符号：{run_draft.deps}"
    )
    assert any(
        u["symbol_id"] == sid("demo", "app.py", "run")
        and u["call"] == "helper"
        for u in result.unresolved_calls
    )


# ---------- 2b. 多符号模块的模块限定调用（可信目标去重）----------
def test_module_qualified_call_with_multi_symbol_module(
    tmp_path: Path, config, store
):
    """同文件多符号不得因模块文件列表重复而误判歧义（可信目标仍可解析）。"""
    root = _write(tmp_path / "repo", {
        "a.py": "def h1():\n    return 1\n\ndef helper():\n    return 2\n",
        "m.py": "import a\n\n\ndef go():\n    return a.helper()\n",
    })
    result = parse_repo(root, "demo", config)
    go = next(d for d in result.symbols if d.qualified_name == "go")
    assert go.deps == [sid("demo", "a.py", "helper")], (
        f"多符号模块的模块限定调用被误判：{go.deps}"
    )


# ---------- 3. 可信目标（success 文件）仍正常建边 ----------
def test_trusted_helper_in_success_file_still_resolves(
    tmp_path: Path, config, store
):
    root = _write(tmp_path / "repo", {
        "core.py": "def helper():\n    return 1\n",
        "app.py": APP_RUN,
    })
    result = parse_repo(root, "demo", config)
    run_draft = next(
        d for d in result.symbols if d.symbol_id == sid("demo", "app.py", "run")
    )
    assert run_draft.deps == [sid("demo", "core.py", "helper")]
    mgr = _manager(store, config, tmp_path)
    mgr.sync(root, "demo")
    assert store.direct_deps(sid("demo", "app.py", "run")) == [
        sid("demo", "core.py", "helper")
    ]
    assert _dangling_edge_count(store) == 0


# ---------- 4. partial 恢复 success 后，下一次同步正常建边 ----------
def test_recovery_sync_builds_dependency_after_healed_parse(
    tmp_path: Path, config, store
):
    root = tmp_path / "repo"
    _write(root, {"broken.py": BROKEN_WITH_HELPER, "app.py": APP_RUN})
    mgr = _manager(store, config, tmp_path)
    out1 = mgr.sync(root, "demo")
    assert store.direct_deps(sid("demo", "app.py", "run")) == []
    assert sid("demo", "broken.py", "helper") in [
        d["symbol_id"] for d in out1.incomplete_symbols
    ]

    # 恢复完整解析
    _write(root, {"broken.py": FIXED_HELPER, "app.py": APP_RUN})
    out2 = mgr.sync(root, "demo")
    assert sid("demo", "broken.py", "helper") in out2.inserted
    assert store.get(sid("demo", "broken.py", "helper")).validity == (
        Validity.VALID.value
    )
    assert sid("demo", "app.py", "run") in out2.deps_refreshed, (
        "恢复后下一次同步应刷新依赖并建边"
    )
    assert store.direct_deps(sid("demo", "app.py", "run")) == [
        sid("demo", "broken.py", "helper")
    ]
    assert _dangling_edge_count(store) == 0
    assert _dangling_deps_count(store) == 0


# ---------- 5. 已注册目标在文件 partial 期间：依赖边保留（不误剪）----------
def test_registered_target_edge_kept_while_target_file_partial(
    tmp_path: Path, config, store
):
    root = tmp_path / "repo"
    _write(root, {"core.py": "def helper():\n    return 1\n", "app.py": APP_RUN})
    mgr = _manager(store, config, tmp_path)
    mgr.sync(root, "demo")
    assert store.direct_deps(sid("demo", "app.py", "run")) == [
        sid("demo", "core.py", "helper")
    ]

    # core.py 进入 partial（helper 已注册 → 无法确认消失 → 保留边）
    _write(root, {"core.py": BROKEN_WITH_HELPER, "app.py": APP_RUN})
    out = mgr.sync(root, "demo")
    assert out.deps_refreshed == []
    assert store.direct_deps(sid("demo", "app.py", "run")) == [
        sid("demo", "core.py", "helper")
    ]
    assert _dangling_edge_count(store) == 0


# ---------- 6. 历史遗留悬空边：同步剪除 + verify 安全拒绝 ----------
def test_legacy_dangling_edge_pruned_and_verify_refuses(
    tmp_path: Path, config, store
):
    root = _write(tmp_path / "repo", {
        "broken.py": BROKEN_WITH_HELPER,
        "app.py": APP_RUN,
    })
    mgr = _manager(store, config, tmp_path)
    mgr.sync(root, "demo")
    run_id = sid("demo", "app.py", "run")
    # 模拟旧实现遗留：人为植入指向未注册 partial 符号的边
    store.set_deps(run_id, [sid("demo", "broken.py", "helper")])
    store.commit()
    assert _dangling_edge_count(store) == 1

    # verify：缺失依赖 → 门控拒绝恢复 valid（安全处理，不崩溃）
    result = mgr.verify(run_id, root)
    assert result == Validity.UNVERIFIED.value
    events = JsonlLogger.read_all(tmp_path / "inv.jsonl")
    blocked = [e for e in events if e["event"] == "verify_blocked"]
    assert blocked
    assert any(
        "missing from store" in r for r in blocked[-1]["dep_reasons"]
    )

    # 下一次同步：悬空边被剪除（仅剪未注册目标，不是清空所有依赖）
    out = mgr.sync(root, "demo")
    assert run_id in out.deps_refreshed
    assert store.direct_deps(run_id) == []
    assert _dangling_edge_count(store) == 0
    assert _dangling_deps_count(store) == 0
    # 其他符号的合法依赖不受影响（非“全清空”规避）
    assert store.get(run_id) is not None
