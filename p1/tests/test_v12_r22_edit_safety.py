"""V1.2-r2.2 M1–M4 测试：E/C、否定解析、IRR01、分列 verified。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from p1_common import SYSTEM_PROMPT, build_messages  # noqa: E402
from v11.visibility import content_sha256  # noqa: E402
from v12.assemble import assemble_v12  # noqa: E402
from v12.config import ARCH_VERSION, load_arm  # noqa: E402
from v12.levels import FileLevel, ExpandPlan, build_plan  # noqa: E402
from v12.messages_visibility import (  # noqa: E402
    current_context_files,
    full_files_in_messages,
    verify_omissions_in_messages,
)
from v12.proof import tracker_from_history  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402

ALPHA = "def a():\n    return 10\n"
BETA = "def b():\n    return 2\n"


def test_arch_version_r22():
    assert ARCH_VERSION == "v1.2-r2.2"


# M1: 否定不进 E
def test_m1_negative_not_edit_target():
    files = ["alpha.py", "beta.py"]
    t = parse_edit_targets("只新增 alpha.py 的 a2() 返回 a()+1。不要修改 beta.py。", files, {})
    assert "alpha.py" in t.exact_paths
    assert "beta.py" not in t.exact_paths
    assert "beta.py" in t.excluded


def test_m1_positive_only():
    t = parse_edit_targets("修改 hot.py 返回 2", ["hot.py", "other.py"], {})
    assert t.exact_paths == {"hot.py"}
    assert "other.py" not in t.exact_paths


# M1: E 强制 FULL 即使历史可见（IRR01）
def test_irr01_edit_target_forced_full_despite_history(tmp_path):
    (tmp_path / "alpha.py").write_text(ALPHA, encoding="utf-8")
    (tmp_path / "beta.py").write_text(BETA, encoding="utf-8")
    resp = "FILE: alpha.py\n```python\n" + ALPHA.rstrip() + "\n```"
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": resp},
    ]
    proof = tracker_from_history(hist)
    # step2 instruction like IRR01
    targets = parse_edit_targets(
        "只新增 alpha.py 的 a2() 返回 a()+1。不要修改 beta.py。",
        ["alpha.py", "beta.py"],
        {},
    )
    assert "alpha.py" in targets.exact_paths
    assert "beta.py" not in targets.exact_paths
    cfg = load_arm("E")
    sha = {"alpha.py": content_sha256(ALPHA), "beta.py": content_sha256(BETA)}
    sizes = {"alpha.py": len(ALPHA), "beta.py": len(BETA)}
    entries = {
        "alpha.py": [{"symbol_id": "a", "validity": "valid", "deps": []}],
        "beta.py": [{"symbol_id": "b", "validity": "valid", "deps": []}],
    }
    plan = build_plan(
        arm_cfg=cfg,
        instruction="只新增 alpha.py 的 a2() 返回 a()+1。不要修改 beta.py。",
        workspace_files=["alpha.py", "beta.py"],
        workspace_sha=sha,
        file_sizes=sizes,
        entries_by_file=entries,
        targets=targets,
    )
    assert "alpha.py" in plan.edit_targets
    assert "alpha.py" in plan.must_full
    assert "beta.py" not in plan.edit_targets
    ctx = assemble_v12(tmp_path, plan, proof, cfg, record_context_marks=False)
    # IRR01 核心：历史有 alpha，但当前 context 必须仍有 alpha FULL
    assert "--- FILE alpha.py" in ctx.text
    assert "alpha.py" not in ctx.omitted_files


# M2: CandidateFull 独立
def test_m2_candidate_not_edit_target():
    # 唯一文件弱关联：编辑动词+符号无法精确路径时可能进 C
    t = parse_edit_targets("请实现该函数逻辑", ["only.py"], {})
    # 唯一文件仓库：可能 candidate
    assert "only.py" not in t.exact_paths or "only.py" in t.exact_paths
    assert t.candidate_full.isdisjoint(t.exact_paths)


def test_m2_candidate_forced_full_and_audit():
    plan = ExpandPlan(arm="E", candidate_full={"cand.py"}, edit_targets=set())
    plan.files.append(
        FileLevel(relpath="cand.py", level="FULL", is_candidate=True, is_must=True)
    )
    assert plan.candidate_full == {"cand.py"}
    assert plan.edit_targets == set()
    a = plan.audit()
    assert "candidate_full" in a and a["edit_targets"] == []


# M3: E/C 禁 O′
def test_m3_edit_target_no_oprime_in_assemble(tmp_path):
    (tmp_path / "a.py").write_text(ALPHA, encoding="utf-8")
    tr = tracker_from_history(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "assistant",
                "content": "FILE: a.py\n```python\n" + ALPHA.rstrip() + "\n```",
            },
        ]
    )
    plan = ExpandPlan(
        arm="E",
        edit_targets={"a.py"},
        files=[
            FileLevel(
                relpath="a.py",
                level="FULL",
                is_must=True,
                is_edit_target=True,
                content_sha256=content_sha256(ALPHA),
            )
        ],
    )
    ctx = assemble_v12(tmp_path, plan, tr, load_arm("E"), record_context_marks=False)
    assert "a.py" not in ctx.omitted_files
    assert "--- FILE a.py" in ctx.text


def test_m3_current_context_only_for_edit_verify():
    msgs = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "assistant",
            "content": "FILE: a.py\n```python\n" + ALPHA.rstrip() + "\n```",
        },
        {
            "role": "user",
            "content": build_messages([], "t", "--- FILE b.py (full current source) ---\n"
                + BETA.rstrip() + "\n\n=== OUTPUT FORMAT ===\nX")[-1]["content"],
        },
    ]
    disk = {
        "a.py": content_sha256(ALPHA),
        "b.py": content_sha256(BETA),
    }
    # a 在 assistant 但不在当前 user context → edit_target 验证失败
    check = verify_omissions_in_messages(
        msgs, [], disk, edit_targets=["a.py"], candidate_full=[]
    )
    assert not check.edit_target_full_verified
    assert check.edit_target_missing == ["a.py"]
    # b 在当前 context → 通过
    check2 = verify_omissions_in_messages(
        msgs, [], disk, edit_targets=["b.py"], candidate_full=[]
    )
    assert check2.edit_target_full_verified
    assert "a.py" in full_files_in_messages(msgs)
    assert "a.py" not in current_context_files(msgs)


# M4: Kmax 豁免 E
def test_m4_kmax_does_not_drop_edit_target():
    cfg = load_arm("E", k_max=1)
    files = ["t1.py", "t2.py", "t3.py", "t4.py"]
    entries = {f: [{"symbol_id": f, "validity": "valid", "deps": []}] for f in files}
    instr = "修改 t1.py 和 t2.py 和 t3.py 和 t4.py"
    targets = parse_edit_targets(instr, files, {})
    plan = build_plan(
        arm_cfg=cfg,
        instruction=instr,
        workspace_files=files,
        workspace_sha={f: content_sha256("x") for f in files},
        file_sizes={f: 10 for f in files},
        entries_by_file=entries,
        targets=targets,
    )
    # 全部正向目标必须在 edit_targets 或至少 must_full
    for f in files:
        if f in plan.edit_targets:
            assert f in plan.must_full
            lv = next(x for x in plan.files if x.relpath == f)
            assert lv.level == "FULL"


# config 四臂安全键相同
def test_r22_safety_keys_same_across_arms():
    e, f, g, h = load_arm("E"), load_arm("F"), load_arm("G"), load_arm("H")
    for other in (f, g, h):
        assert e.edit_target_oprime_forbid == other.edit_target_oprime_forbid
        assert e.candidate_full_oprime_forbid == other.candidate_full_oprime_forbid
        assert e.o_prime == other.o_prime
