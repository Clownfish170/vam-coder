"""ICG 单元测试：extract 确定性、预算、与 must 不冲突。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cr.icg import (  # noqa: E402
    ICGCandidate,
    detect_extract_intent,
    path_extract_intent,
    select_optional_full,
)
from v11.visibility import content_sha256  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import build_plan  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402


def test_detect_extract_intent():
    assert detect_extract_intent("请把 limits.py 中的 MAX 写死到 main.py")
    assert not detect_extract_intent("请修改 main.py 中的 clamp")


def test_path_extract_requires_clause_mention():
    instr = "请把 limits.py 中的 MAX 写死到 main.py。不要修改 junk.py。"
    assert path_extract_intent("limits.py", instr)
    assert not path_extract_intent("junk.py", instr)


def test_greedy_selects_extract_and_respects_budget():
    cands = [
        ICGCandidate(path="limits.py", size_bytes=80, instruction_hit=True, extract_intent=True),
        ICGCandidate(path="noise_big.py", size_bytes=4000, r_score=1),
        ICGCandidate(path="ok.py", size_bytes=40, instruction_hit=True),
    ]
    res = select_optional_full(
        cands, instruction="把 limits.py 的值写死", budget_tokens=50
    )
    assert "limits.py" in res.selected  # forced
    assert "noise_big.py" in res.skipped  # too big for budget after force


def test_icg_arm_plan_drops_non_selected_related():
    files = ["hot.py", "need_rates.py", "noise.py"]
    srcs = {
        "hot.py": "def h():\n    return 1\n",
        "need_rates.py": "X = 1\n",
        "noise.py": "def n():\n    return 0\n",
    }
    instruction = "请把 need_rates.py 中的 X 写死到 hot.py。不要修改 noise.py。"
    targets = parse_edit_targets(instruction, files, {})
    cfg = load_arm("V13AICG")
    assert cfg.icg_enabled
    sha = {f: content_sha256(srcs[f]) for f in files}
    sizes = {f: len(srcs[f]) for f in files}
    entries = {
        f: [{"symbol_id": f"e:{f}", "validity": "valid", "deps": []}] for f in files
    }
    plan = build_plan(
        arm_cfg=cfg,
        instruction=instruction,
        workspace_files=files,
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        system_history_tokens_est=0,
        source_by_file=srcs,
    )
    by = {f.relpath: f for f in plan.files}
    # ET full
    assert by["hot.py"].level == "FULL"
    # extract related 保持 FULL
    assert by["need_rates.py"].level == "FULL"
    assert by["need_rates.py"].reason in ("icg_full", "edit_target", "must_full", "related_full")
    # noise：否定 + 无 extract → 应被 ICG 跳过或本就 unrelated
    assert by["noise.py"].level == "NONE"


def test_f_arm_unchanged_by_icg():
    files = ["hot.py", "need_rates.py", "noise.py"]
    srcs = {
        "hot.py": "def h():\n    return 1\n",
        "need_rates.py": "X = 1\n",
        "noise.py": "def n():\n    return 0\n",
    }
    instruction = "请把 need_rates.py 中的 X 写死到 hot.py。"
    targets = parse_edit_targets(instruction, files, {})
    cfg = load_arm("F")
    assert not cfg.icg_enabled
    sha = {f: content_sha256(srcs[f]) for f in files}
    sizes = {f: len(srcs[f]) for f in files}
    entries = {
        f: [{"symbol_id": f"e:{f}", "validity": "valid", "deps": []}] for f in files
    }
    plan = build_plan(
        arm_cfg=cfg,
        instruction=instruction,
        workspace_files=files,
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
        system_history_tokens_est=0,
        source_by_file=srcs,
    )
    # F：相关 need_rates 应为 FULL（r>0）
    by = {f.relpath: f for f in plan.files}
    assert by["need_rates.py"].level == "FULL"


def test_v13b_is_iteration_of_v13a():
    """V13B 必须继承 V13A 的 C 库，并在 related 上升级为 ICG。"""
    from v12.config import config_diff, load_arm

    v13a = load_arm("V13ACR")
    v13b = load_arm("V13BICG")
    # 继承 V13A
    assert v13b.cr_enabled is True
    assert v13a.cr_enabled is True
    # 相对 V13A：打开 ICG，related 不再一律 skip（mode→full，由 plan 层 ICG 裁决）
    d = config_diff(v13a, v13b)
    assert "icg_enabled" in d
    assert v13b.icg_enabled and not v13a.icg_enabled
    assert v13b.cr_related_mode == "full"
    # 相对 F：多出 cr + icg（迭代自 V12-F 路径上的 V13A 能力）
    df = config_diff(load_arm("F"), v13b)
    assert "cr_enabled" in df and "icg_enabled" in df


def test_retrieval_finds_symbol():
    from cr.retrieval import build_file_index, retrieve_candidates

    files = {
        "cfg.py": "LIMIT = 42\ndef get_limit():\n    return LIMIT\n",
        "app.py": "def run():\n    return 0\n",
    }
    idx = build_file_index(files)
    hits = retrieve_candidates("请读取 get_limit 的值", idx, universe=set(files))
    assert "cfg.py" in hits


def test_osca_lambda_increases_with_usage():
    from cr.osca import OscState, update_lambda

    st = OscState(lam=0.02, used_tokens=0, alpha=0.05, rho=0.1)
    update_lambda(st, budget_tokens=100)
    assert st.lam >= 0.02
    st.used_tokens = 80
    update_lambda(st, budget_tokens=100)
    # 占用超 rho → lam 上升
    assert st.lam > 0.02


def test_v13bsp_has_osca_and_retrieval():
    from v12.config import config_diff, load_arm

    b = load_arm("V13BSP")
    tp = load_arm("V13BTESTPART")
    assert b.osca_enabled and b.retrieval_enabled and b.icg_enabled and b.cr_enabled
    d = config_diff(tp, b)
    assert "osca_enabled" in d and "retrieval_enabled" in d
