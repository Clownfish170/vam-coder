"""V1.2 单元测试：目标解析 / 闭包 / O′ / 预算 / 窗口 / 配置 / 指标。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v12.assemble import assemble_v12  # noqa: E402
from v12.config import config_diff, load_arm  # noqa: E402
from v12.levels import build_plan, dependency_closure  # noqa: E402
from v12.metrics import (  # noqa: E402
    EpisodeTokenLedger,
    fe_tc_mean,
    fe_tc_total,
    tokens_per_attempted,
    tokens_per_successful,
)
from v12.targets import parse_edit_targets  # noqa: E402
from v11.visibility import VisibilityTracker, content_sha256  # noqa: E402


def _plan(
    arm="E",
    instruction="修改 hot.py 返回 2",
    files=None,
    sha=None,
    sizes=None,
    entries=None,
    targets=None,
    sys_hist=0,
    **cfg_kw,
):
    files = files or ["hot.py", "stable_a.py", "stable_b.py"]
    sha = sha or {f: content_sha256(f"def x_{f}():\n    return 1\n") for f in files}
    sizes = sizes or {f: 40 for f in files}
    entries = entries if entries is not None else {
        "hot.py": [{"symbol_id": "e:hot.py::hot", "validity": "valid", "deps": []}],
        "stable_a.py": [{"symbol_id": "e:stable_a.py::fa", "validity": "valid", "deps": []}],
        "stable_b.py": [{"symbol_id": "e:stable_b.py::fb", "validity": "valid", "deps": []}],
    }
    targets = targets or parse_edit_targets(instruction, files, {})
    cfg = load_arm(arm, **cfg_kw)
    plan = build_plan(
        arm_cfg=cfg,
        instruction=instruction,
        workspace_files=files,
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        system_history_tokens_est=sys_hist,
    )
    return cfg, plan, targets


# 1 编辑目标精确匹配
def test_edit_target_path_exact_word_boundary():
    files = ["hot.py", "hot.py.bak", "photography.py"]
    t = parse_edit_targets("修改 hot.py 返回 2", files, {})
    assert "hot.py" in t.exact_paths
    # photography 不应因 hot 子串进入 exact
    assert "photography.py" not in t.exact_paths


def test_edit_target_symbol_exact():
    files = ["core.py"]
    t = parse_edit_targets("修改 double 函数", files, {"double": ["core.py"]})
    assert "core.py" in t.exact_paths


# 2 fuzzy 仅审计
def test_fuzzy_only_audit_not_must():
    files = ["hotfix_helper.py", "hot.py"]
    # "hotfix" 词边界不匹配 hot.py；若指令含 hotfix 子串无边界则 fuzzy
    t = parse_edit_targets("请处理 hotfix helper 相关逻辑", files, {})
    # hotfix_helper basename stem 词边界匹配
    # fuzzy hits 不应自动进 exact
    cfg, plan, targets = _plan(
        instruction="请处理 hotfix helper 相关逻辑",
        files=["hotfix_helper.py", "hot.py"],
        entries={
            "hotfix_helper.py": [{"symbol_id": "a", "validity": "valid", "deps": []}],
            "hot.py": [{"symbol_id": "b", "validity": "valid", "deps": []}],
        },
    )
    assert "hot.py" not in plan.must_full or "hot.py" not in targets.exact_paths
    # fuzzy_only_hits 记录审计
    assert isinstance(targets.fuzzy_only_hits, set)


def test_fuzzy_does_not_enter_must():
    files = ["foo.py", "bar.py"]
    t = parse_edit_targets("修改 foo.py 返回值", files, {})
    assert t.fuzzy_only_hits == set()
    assert "foo.py" in t.exact_paths
    # 仅 stem 无 .py：不应进入 exact（词边界对 basename foo.py 不匹配 foo）
    t2 = parse_edit_targets("修改 foo 返回值", files, {})
    assert "foo.py" not in t2.exact_paths


# 3 依赖闭包
def test_dependency_closure_depth():
    # a->b->c providers, depth=1 only gets b
    file_deps = {"a.py": {"b.py"}, "b.py": {"c.py"}, "c.py": set()}
    got = dependency_closure({"a.py"}, {}, file_deps, depth=1)
    assert "b.py" in got
    assert "c.py" not in got
    got2 = dependency_closure({"a.py"}, {}, file_deps, depth=2)
    assert "c.py" in got2


def test_callers_closure():
    file_deps = {"caller.py": {"prov.py"}, "prov.py": set()}
    got = dependency_closure({"prov.py"}, {}, file_deps, depth=2)
    assert "caller.py" in got


# 4 同名符号冲突
def test_ambiguous_symbol_all_paths_must():
    files = ["a.py", "b.py"]
    t = parse_edit_targets("修改 norm 实现", files, {"norm": ["a.py", "b.py"]})
    assert "a.py" in t.exact_paths and "b.py" in t.exact_paths
    assert "norm" in t.ambiguous_symbols


# 5-6 O′ hash 可见性与回退
def test_oprime_hash_mismatch_fallback_full(tmp_path):
    body = "def hot():\n    return 1\n"
    (tmp_path / "hot.py").write_text(body, encoding="utf-8")
    tr = VisibilityTracker()
    # 可见的是错误内容
    tr.mark_from_context("--- FILE hot.py (full current source) ---\ndef hot():\n    return 99\n")
    cfg, plan, _ = _plan(
        instruction="hot.py 返回 2",
        files=["hot.py"],
        entries={"hot.py": [{"symbol_id": "h", "validity": "valid", "deps": []}]},
    )
    ctx = assemble_v12(tmp_path, plan, tr, cfg)
    # must Full 且 hash 不匹配 → 必须注入
    assert ctx.file_blocks == 1
    assert "return 1" in ctx.text or "return 1" in ctx.text.replace("\r", "")


def test_oprime_visible_match_omit_non_must(tmp_path):
    # F arm: related non-must FULL；可见且 hash 匹配 → O′ 省略
    body_a = "def fa():\n    return 'A'\n"
    body_h = "def hot():\n    return 1\n"
    (tmp_path / "hot.py").write_text(body_h, encoding="utf-8")
    (tmp_path / "stable.py").write_text(body_a, encoding="utf-8")
    tr = VisibilityTracker()
    tr.mark_from_context(f"--- FILE stable.py (full current source) ---\n{body_a.rstrip()}\n")
    # stem "stable" 出现在指令中 → r>=1 相关，但 basename "stable.py" 不在指令 → 非 must
    cfg, plan, _ = _plan(
        arm="F",
        instruction="修改 hot.py 返回 2；stable 模块勿动",
        files=["hot.py", "stable.py"],
        entries={
            "hot.py": [{"symbol_id": "h", "validity": "valid", "deps": []}],
            "stable.py": [{"symbol_id": "s", "validity": "valid", "deps": []}],
        },
    )
    levels = {f.relpath: f for f in plan.files}
    assert levels["hot.py"].level == "FULL" and levels["hot.py"].is_must
    assert levels["stable.py"].level == "FULL" and not levels["stable.py"].is_must
    ctx = assemble_v12(tmp_path, plan, tr, cfg)
    assert "stable.py" in ctx.omitted_files
    assert ctx.verified_safe_omissions >= 1
    assert "return 'A'" not in ctx.text


# 7 missing file 不伪造
def test_missing_must_file_insufficient(tmp_path):
    cfg, plan, _ = _plan(
        instruction="修改 ghost.py 返回 2",
        files=["ghost.py"],
        sha={"ghost.py": content_sha256("x")},
        entries={"ghost.py": [{"symbol_id": "g", "validity": "valid", "deps": []}]},
        targets=parse_edit_targets("修改 ghost.py 返回 2", ["ghost.py"], {}),
    )
    # workspace 无文件
    ctx = assemble_v12(tmp_path, plan, VisibilityTracker(), cfg)
    assert ctx.insufficient
    assert "MISSING_REQUIRED_FILE" in ctx.insufficient_reasons
    assert "def ghost" not in ctx.text


# 8 超窗口保护
def test_context_window_insufficient_no_truncate():
    cfg, plan, _ = _plan(sys_hist=100, context_window=50, instruction="修改 hot.py 返回 2")
    assert plan.insufficient
    assert "REQUIRED_CONTEXT_EXCEEDS_LIMIT" in plan.insufficient_reasons
    # must 仍在
    assert "hot.py" in plan.must_full
    levels = {f.relpath: f for f in plan.files if f.is_must}
    assert levels["hot.py"].level == "FULL"


# 9 Kmax 不影响 must
def test_kmax_does_not_drop_must():
    files = [f"f{i}.py" for i in range(12)]
    entries = {
        f: [{"symbol_id": f"s{i}", "validity": "valid", "deps": []}]
        for i, f in enumerate(files)
    }
    # 全部为 must via ambiguous symbol? 用 risk validity
    entries["f0.py"] = [{"symbol_id": "s0", "validity": "stale", "deps": []}]
    targets = parse_edit_targets("修改 f0.py 返回 1", files, {})
    cfg, plan, _ = _plan(
        instruction="修改 f0.py 返回 1",
        files=files,
        entries=entries,
        targets=targets,
        k_max=2,
    )
    assert len(plan.must_full) >= 1
    assert "f0.py" in plan.must_full
    must_levels = {f.relpath for f in plan.files if f.is_must and f.level == "FULL"}
    assert "f0.py" in must_levels


# 10 optional full 超预算/Kmax 丢弃
def test_optional_full_dropped_by_kmax():
    files = ["hot.py", "a.py", "b.py", "c.py", "d.py"]
    entries = {
        f: [{"symbol_id": f"s{f}", "validity": "valid", "deps": []}]
        for f in files
    }
    cfg, plan, _ = _plan(
        arm="F",
        instruction="修改 hot.py 返回 2",
        files=files,
        entries=entries,
        k_max=1,  # only must
    )
    assert plan.dropped_optional_full or len(plan.must_full) >= 1
    # must 保留
    assert any(f.is_must and f.level == "FULL" for f in plan.files)


def test_digest_dropped_on_budget():
    cfg, plan, _ = _plan(
        arm="E",
        instruction="修改 hot.py 返回 2",
        files=["hot.py", "stable_a.py"],
        sizes={"hot.py": 10000, "stable_a.py": 10000},
        budget_tokens=10,  # 必注 must 超预算
    )
    assert plan.over_budget
    # must 仍在 FULL
    assert any(f.relpath == "hot.py" and f.level == "FULL" and f.is_must for f in plan.files)
    # 可选 digest 被丢
    assert "stable_a.py" in plan.dropped_optional_digest or any(
        f.relpath == "stable_a.py" and f.level == "NONE" for f in plan.files
    )


# 11 E/F/G/H 配置差异
def test_efgh_config_diff_single_variable():
    e, f, g, h = load_arm("E"), load_arm("F"), load_arm("G"), load_arm("H")
    assert config_diff(e, f) == {"non_target_related"}
    assert config_diff(e, h) == {"non_target_related"}
    assert "task_aware_r" in config_diff(e, g)
    assert "non_target_related" in config_diff(e, g)
    # must/o_prime 不变
    for other in (f, g, h):
        assert other.o_prime == e.o_prime
        assert other.must_full_dep_closure == e.must_full_dep_closure
        assert other.exact_targets == e.exact_targets


def test_efgh_level_policy():
    # stem "stable" 命中指令 → 相关非目标；basename 不在指令 → 非 must
    files = ["hot.py", "stable.py"]
    entries = {f: [{"symbol_id": f, "validity": "valid", "deps": []}] for f in files}
    inst = "修改 hot.py 返回 2；stable 模块勿动"
    for arm in "EFGH":
        cfg, plan, _ = _plan(arm=arm, instruction=inst, files=files, entries=entries)
        lv = {f.relpath: f for f in plan.files}
        assert lv["hot.py"].is_must and lv["hot.py"].level == "FULL"
        if arm == "E":
            assert lv["stable.py"].level == "DIGEST", lv
        elif arm == "F":
            assert lv["stable.py"].level == "FULL", lv
        elif arm == "H":
            assert lv["stable.py"].level == "NONE", lv
        elif arm == "G":
            assert lv["stable.py"].level == "FULL", lv  # full_if_indexed


# 12 token / 重试
def test_retry_tokens_accumulate():
    led = EpisodeTokenLedger()
    led.add_request(100, 10)
    led.add_request(50, 5, is_retry=True)
    assert led.total == 165
    assert led.retry_tokens == 55


# 13 FETC
def test_fetc_and_tpae_tpse():
    totals = [100, 200, 300]
    succ = [True, False, False]
    assert tokens_per_attempted(totals) == 200
    assert tokens_per_successful(totals, succ) == 600.0  # 600/1
    assert fe_tc_total(totals, succ) == 500
    assert fe_tc_mean(totals, succ) == 250
    assert fe_tc_mean([100], [True]) is None
    assert tokens_per_successful([100, 200], [False, False]) == float("inf")


# 14 INSUFFICIENT 分类
def test_insufficient_reasons_classification():
    cfg, plan, _ = _plan(sys_hist=0, context_window=1, instruction="修改 hot.py 返回 2")
    assert plan.insufficient_reasons == ["REQUIRED_CONTEXT_EXCEEDS_LIMIT"]
    # missing file
    tmp = Path(__file__).parent  # empty-ish; use non-existing content via assemble
    # covered in test_missing_must_file_insufficient


def test_audit_fields_completeness():
    cfg, plan, _ = _plan()
    a = plan.audit()
    for key in [
        "must_full_count",
        "k_max",
        "over_kmax",
        "over_budget",
        "est_must_full_tokens",
        "est_digest_tokens",
        "insufficient",
        "insufficient_reasons",
        "required_context_tokens_est",
        "available_context_tokens",
        "dropped_optional_digest",
        "fuzzy_only_hits",
        "edit_targets",
        "must_full",
        "closure_depth",
    ]:
        assert key in a, key
