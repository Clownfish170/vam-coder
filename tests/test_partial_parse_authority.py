"""任务 1 回归测试：部分 AST（partial parse）不得作为权威快照更新记忆。

覆盖：部分 AST 不覆盖已有内容哈希/依赖/有效状态、解析残缺不误 tombstone、
部分文件中的新符号不注册为完整记忆（仅诊断）、解析恢复后重新允许完整
同步、verify 在部分解析下保持不结论（旧实现在“符号被提取到”时会直接
写 stale —— 即本任务修复的缺陷）。
读取失败 / 仓库路径错误 / 真实删除 / 不支持语言的区分见 test_parse_guard.py。
"""

from __future__ import annotations

from vam_coder.invalidation import InvalidationManager
from vam_coder.logging_util import JsonlLogger
from vam_coder.models import Action, RouteRequest, Validity
from vam_coder.parser import parse_repo, parse_source
from vam_coder.router import RuleRouter

from conftest import REPO_V1, sid, write_repo

# ---- 构造：语法错误但 tree-sitter 仍部分提取 ----
# case A：compute 被提取（内容已变）+ broken 语法错误
PARTIAL_CHANGED = (
    "def compute(x):\n"
    "    return x * 999\n"
    "\n"
    "def broken(x:\n"
    "    return x\n"
)
# case B：lone 丢失，run 与恢复出的 broken 被提取
PARTIAL_LOST_SYMBOL = (
    "def run(x):\n"
    "    return helper(x)\n"
    "\n"
    "def broken(:\n"
)
# case C：既有 compute + 新符号 extra/broken + 语法错误
PARTIAL_WITH_NEW_SYMBOL = (
    "def compute(x):\n"
    "    return x * 2\n"
    "\n"
    "def extra():\n"
    "    return 1\n"
    "\n"
    "def broken(:\n"
)
# 恢复后的干净 v2（内容 = 变过的 compute，语法完整）
CLEAN_V2_CORE = (
    '"""Core helpers."""\n'
    "\n"
    "\n"
    "def compute(x):\n"
    '    """Compute tripled value."""\n'
    "    return x * 999\n"
    "\n"
    "\n"
    "def helper(x):\n"
    "    return compute(x) + 1\n"
)


def _manager(store, config, tmp_path) -> InvalidationManager:
    return InvalidationManager(store, config, JsonlLogger(tmp_path / "inv.jsonl"))


def test_partial_changed_file_does_not_update_memory_basis(
    store, config, fresh_repo, tmp_path
):
    """部分 AST 中已提取的符号也不得更新哈希/依赖/版本（只可收紧）。"""
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    compute_id = sid("demo", "core.py", "compute")
    helper_id = sid("demo", "core.py", "helper")
    before_c = store.get(compute_id)
    before_h = store.get(helper_id)

    fresh_repo({**REPO_V1, "core.py": PARTIAL_CHANGED})
    out = mgr.sync(repo, "demo")

    # 内容依据、观察哈希、版本、依赖全部保持原状
    after_c = store.get(compute_id)
    assert after_c.content_hash == before_c.content_hash, "部分 AST 覆盖了 content_hash"
    assert after_c.source_hash == before_c.source_hash, "部分 AST 覆盖了 source_hash"
    assert after_c.version == before_c.version == 1, "部分解析不得 bump 版本"
    assert after_c.deps == before_c.deps
    assert store.get(helper_id).deps == before_h.deps, "部分解析不得刷新依赖边"
    # 不得判 stale（stale 意味着“权威观察到变化”）；只可保守收紧为 unverified
    assert after_c.validity == Validity.UNVERIFIED.value, (
        f"partial 只能收紧 unverified，实际 {after_c.validity}"
    )
    assert store.get(helper_id).validity == Validity.UNVERIFIED.value
    # 不产生任何权威更新类目
    assert out.content_changed == []
    assert out.reverted == []
    assert out.deps_refreshed == []
    assert out.tombstoned == []
    assert {u["symbol_id"] for u in out.unconfirmed} >= {compute_id, helper_id}
    assert all(u["reason"] == "file_partial" for u in out.unconfirmed)
    # 收紧后的记忆不得允许 REUSE_KV
    router = RuleRouter(config, JsonlLogger(None))
    actions = router.route(
        RouteRequest(entries=[store.get(compute_id), store.get(helper_id)])
    ).actions()
    assert actions[compute_id] == Action.EXPAND.value
    assert actions[helper_id] == Action.EXPAND.value
    # 诊断：文件状态与原因被保留
    assert any(
        w["path"] == "core.py" and "tree_sitter_has_error" in w["reason"]
        for w in out.parse_warnings
    )


def test_partial_missing_symbol_not_tombstoned(
    store, config, fresh_repo, tmp_path
):
    """部分文件中缺失的既有符号：不 tombstone，保留依据并收紧。"""
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    lone_id = sid("demo", "app.py", "lone")
    before = store.get(lone_id)

    fresh_repo({**REPO_V1, "app.py": PARTIAL_LOST_SYMBOL})
    out = mgr.sync(repo, "demo")

    assert out.tombstoned == [], "partial 文件中的缺失 ≠ 删除"
    lone = store.get(lone_id)
    assert lone.validity == Validity.UNVERIFIED.value
    assert lone.version == before.version == 1
    assert lone.content_hash == before.content_hash
    assert lone.source_hash == before.source_hash
    # run 被部分提取，同样不作权威更新（只可收紧）
    run = store.get(sid("demo", "app.py", "run"))
    assert run.version == 1
    assert run.validity == Validity.UNVERIFIED.value
    assert sid("demo", "app.py", "broken") not in out.inserted


def test_new_symbols_in_partial_file_not_registered(
    store, config, fresh_repo, tmp_path
):
    """部分文件中的新符号：不注册为记忆，只保留诊断。"""
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")

    fresh_repo({**REPO_V1, "core.py": PARTIAL_WITH_NEW_SYMBOL})
    out = mgr.sync(repo, "demo")

    assert store.get(sid("demo", "core.py", "extra")) is None, (
        "partial 文件的新符号不得注册为已验证完整记忆"
    )
    assert store.get(sid("demo", "core.py", "broken")) is None
    assert sid("demo", "core.py", "extra") not in out.inserted
    # 诊断信息保留（不完整/待验证状态）
    diag = {d["symbol_id"]: d for d in out.incomplete_symbols}
    assert sid("demo", "core.py", "extra") in diag
    assert diag[sid("demo", "core.py", "extra")]["status"] == "partial"
    assert diag[sid("demo", "core.py", "extra")]["reason"]
    # 既有符号照旧保守收紧，不覆盖
    assert store.get(sid("demo", "core.py", "compute")).validity == (
        Validity.UNVERIFIED.value
    )
    assert store.get(sid("demo", "core.py", "compute")).version == 1


def test_recovery_after_parse_fixed_resumes_authoritative_sync(
    store, config, fresh_repo, tmp_path
):
    """解析恢复正常后，完整同步重新生效并按既有规则推进。"""
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    compute_id = sid("demo", "core.py", "compute")
    basis = store.get(compute_id).content_hash

    # 1) 部分解析：冻结
    fresh_repo({**REPO_V1, "core.py": PARTIAL_CHANGED})
    out1 = mgr.sync(repo, "demo")
    assert out1.content_changed == []
    assert store.get(compute_id).version == 1

    # 2) 恢复完整解析（内容确实变了）：权威更新恢复
    fresh_repo({**REPO_V1, "core.py": CLEAN_V2_CORE})
    out2 = mgr.sync(repo, "demo")
    assert compute_id in out2.content_changed, "恢复后应按既有规则识别变化"
    entry = store.get(compute_id)
    assert entry.validity == Validity.STALE.value
    assert entry.version == 2
    assert entry.content_hash == basis, "记忆依据仍是原始 v1"
    assert entry.source_hash != basis
    # 依赖传播恢复（helper 经闭包 unverified —— 已由 4.5 规则处理）
    assert store.get(sid("demo", "core.py", "helper")).validity == (
        Validity.UNVERIFIED.value
    )
    # 3) 恢复为原内容：revert 规则生效 → valid
    fresh_repo(dict(REPO_V1))
    out3 = mgr.sync(repo, "demo")
    assert compute_id in out3.reverted
    assert store.get(compute_id).validity == Validity.VALID.value


def test_verify_partial_parse_inconclusive_even_if_symbol_extracted(
    store, config, fresh_repo, tmp_path
):
    """verify 遇到部分解析：即使符号被提取到，也不得写 stale/恢复。"""
    mgr = _manager(store, config, tmp_path)
    repo = tmp_path / "repo"
    mgr.sync(repo, "demo")
    compute_id = sid("demo", "core.py", "compute")
    before = store.get(compute_id)

    fresh_repo({**REPO_V1, "core.py": PARTIAL_CHANGED})
    result = mgr.verify(compute_id, repo)

    assert result == Validity.UNVERIFIED.value, (
        "部分解析是“无法确认”，不是“权威观察到变化”"
    )
    entry = store.get(compute_id)
    assert entry.version == before.version == 1, "verify 不得用部分 AST 写库"
    assert entry.source_hash == before.source_hash
    assert entry.content_hash == before.content_hash
    assert entry.validity == Validity.UNVERIFIED.value


def test_parse_statuses_recorded_per_file(tmp_path, config):
    """逐文件状态：success / partial / failed / unsupported_language。"""
    root = tmp_path / "repo"
    write_repo(root, {
        "ok.py": "def fine():\n    return 1\n",
        "bad.py": "def bad(:\n",
        "app.js": "function f() {}\n",
    })
    result = parse_repo(root, "demo", config)
    assert result.file_status["ok.py"] == "success"
    assert result.file_status["bad.py"] == "partial"
    assert result.file_status["app.js"] == "unsupported_language"
    assert result.file_errors["bad.py"] == "tree_sitter_has_error"
    # failed（读取失败）原因同样保留 —— 由 test_parse_guard 的读失败用例覆盖

    # 部分文件的草稿存在（供诊断与消解），但权威性由状态区分
    drafts, has_error = parse_source(
        b"def x(:\n", "bad.py", "demo", "python"
    )
    assert has_error is True
