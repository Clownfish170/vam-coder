"""O′ 跨步可见性回归测试（T1–T8）+ 阶段 B 发送前验证。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from p1_common import SYSTEM_PROMPT, build_messages, trim_history  # noqa: E402
from v11.visibility import content_sha256  # noqa: E402
from v12.assemble import assemble_v12  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import FileLevel, ExpandPlan  # noqa: E402
from v12.messages_visibility import (  # noqa: E402
    full_files_in_messages,
    verify_omissions_in_messages,
)
from v12.proof import tracker_from_history  # noqa: E402


BODY_A = "def fa():\n    return 1\n"
BODY_B = "def fb():\n    return 2\n"


def _ws(tmp_path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def _plan_full(paths: list[str], is_must: dict[str, bool] | None = None) -> ExpandPlan:
    is_must = is_must or {}
    files = [
        FileLevel(relpath=p, level="FULL", is_must=is_must.get(p, True), reason="test")
        for p in paths
    ]
    return ExpandPlan(arm="E", files=files, must_full={p for p in paths if is_must.get(p, True)})


def _assemble(tmp_path, plan, history, cfg=None, force_full=None):
    cfg = cfg or load_arm("E")
    proof = tracker_from_history(history)
    ctx = assemble_v12(
        tmp_path,
        plan,
        proof,
        cfg,
        force_full=force_full,
        record_context_marks=False,
    )
    trimmed, _, _ = trim_history(history, 24000)
    messages = build_messages(trimmed, "修改 fa 返回 2", ctx.text)
    check = verify_omissions_in_messages(
        messages,
        list(ctx.omitted_files),
        {rel: content_sha256((tmp_path / rel).read_text(encoding="utf-8")) for rel in paths_of(plan)},
    )
    if not check.ok:
        ctx = assemble_v12(
            tmp_path,
            plan,
            proof,
            cfg,
            force_full=set(check.missing_or_mismatch),
            record_context_marks=False,
        )
        messages = build_messages(trimmed, "修改 fa 返回 2", ctx.text)
        check = verify_omissions_in_messages(
            messages,
            list(ctx.omitted_files),
            {rel: content_sha256((tmp_path / rel).read_text(encoding="utf-8")) for rel in paths_of(plan)},
        )
    return ctx, messages, check


def paths_of(plan: ExpandPlan) -> list[str]:
    return [f.relpath for f in plan.files]


# T1 Step1 注入 A，Step2 无 assistant 回写 → 必须 FULL
def test_t1_step2_without_assistant_requires_full(tmp_path):
    _ws(tmp_path, {"a.py": BODY_A})
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_messages([], "t", "--- FILE a.py (full current source) ---\n" + BODY_A.rstrip() + "\n")[-1]["content"],
        },
        # 无 assistant FILE
    ]
    # 模拟 step2 历史：仅 system + NO_EDIT assistant（无 FILE）
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "NO_EDIT"},
    ]
    plan = _plan_full(["a.py"])
    ctx, messages, check = _assemble(tmp_path, plan, hist)
    assert "a.py" not in ctx.omitted_files
    assert check.ok
    assert "a.py" in full_files_in_messages(messages)


# T2 assistant 回写 A 且 hash 一致 → 允许 O′
def test_t2_assistant_echo_allows_omit(tmp_path):
    _ws(tmp_path, {"a.py": BODY_A})
    resp = "FILE: a.py\n```python\n" + BODY_A.rstrip() + "\n```"
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": resp},
    ]
    plan = _plan_full(["a.py"])
    ctx, messages, check = _assemble(tmp_path, plan, hist)
    assert "a.py" in ctx.omitted_files
    assert check.ok  # 仍能在 messages 中找到完整 a.py
    # 省略后 user 不再注入，但 assistant 仍有 FILE
    blocks = full_files_in_messages(messages)
    assert content_sha256(blocks["a.py"]) == content_sha256(BODY_A)


# T3 assistant 回写但 trim_history 裁掉 → 必须 FULL
def test_t3_trim_history_revokes_proof(tmp_path):
    _ws(tmp_path, {"a.py": BODY_A, "big.py": "x" * 5000})
    resp = "FILE: a.py\n```python\n" + BODY_A.rstrip() + "\n```"
    # 构造超长历史迫使 trim 丢掉 assistant
    long_user = {"role": "user", "content": "Y" * 30000}
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": long_user["content"]},
        {"role": "assistant", "content": resp},
    ]
    trimmed, dropped, _ = trim_history(hist, 500)
    # 确保被裁或至少验证：proof 来自 trimmed 而非全 hist
    proof = tracker_from_history(trimmed)
    if not proof.has_visible("a.py", content_sha256(BODY_A)):
        plan = _plan_full(["a.py"])
        ctx = assemble_v12(
            tmp_path,
            plan,
            proof,
            load_arm("E"),
            record_context_marks=False,
        )
        assert "a.py" not in ctx.omitted_files
    else:
        # 若 trim 未裁掉（实现边界），用 max_history 强制裁掉
        trimmed2, _, _ = trim_history(
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "assistant", "content": resp}],
            10,
        )
        proof2 = tracker_from_history(trimmed2)
        plan = _plan_full(["a.py"])
        ctx = assemble_v12(tmp_path, plan, proof2, load_arm("E"), record_context_marks=False)
        assert "a.py" not in ctx.omitted_files or not proof2.has_visible(
            "a.py", content_sha256(BODY_A)
        )


# T4 CFD01 双 must：无历史证明 → 两文件均 FULL
def test_t4_cfd01_dual_must_no_stale_context_omit(tmp_path):
    _ws(tmp_path, {"invoice.py": "def g():\n    return 1\n", "tax.py": "def t():\n    return 0.5\n"})
    hist = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "assistant", "content": "NO_EDIT"}]
    plan = _plan_full(["invoice.py", "tax.py"])
    ctx, messages, check = _assemble(tmp_path, plan, hist)
    assert ctx.omitted_files == []
    assert ctx.file_blocks == 2
    vis = full_files_in_messages(messages)
    assert "invoice.py" in vis and "tax.py" in vis


# T5 仅 INDEX/DIGEST 不能证明 FULL 可见
def test_t5_digest_not_full_proof(tmp_path):
    _ws(tmp_path, {"a.py": BODY_A})
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "--- INDEX a.py ---"},
    ]
    # 即便错误地把 INDEX 文本当 context，也不应含 FILE body
    proof = tracker_from_history(hist)
    assert not proof.has_visible("a.py", content_sha256(BODY_A))
    plan = _plan_full(["a.py"])
    ctx = assemble_v12(tmp_path, plan, proof, load_arm("E"), record_context_marks=False)
    assert "a.py" not in ctx.omitted_files


# T6 hash 不一致 → FULL 回退
def test_t6_hash_mismatch_full(tmp_path):
    _ws(tmp_path, {"a.py": BODY_A})
    wrong = "def fa():\n    return 99\n"
    resp = "FILE: a.py\n```python\n" + wrong.rstrip() + "\n```"
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": resp},
    ]
    plan = _plan_full(["a.py"])
    ctx, messages, check = _assemble(tmp_path, plan, hist)
    # 候选可能 omit（hash 与 disk 不同则 phase_a 不 omit）
    # disk hash != visible → 不 omit
    assert "a.py" not in ctx.omitted_files
    assert check.ok
    blocks = full_files_in_messages(messages)
    assert content_sha256(blocks["a.py"]) == content_sha256(BODY_A)


# T7 must 缺失 → INSUFFICIENT
def test_t7_missing_must_insufficient(tmp_path):
    plan = _plan_full(["ghost.py"])
    proof = tracker_from_history([{"role": "system", "content": SYSTEM_PROMPT}])
    ctx = assemble_v12(tmp_path, plan, proof, load_arm("E"), record_context_marks=False)
    assert ctx.insufficient
    assert "MISSING_REQUIRED_FILE" in ctx.insufficient_reasons


# T8 发送前 messages 与 snapshot 一致；修订后 omitted 在 messages 中有完整源码
def test_t8_presend_snapshot_consistent(tmp_path):
    _ws(tmp_path, {"a.py": BODY_A, "b.py": BODY_B})
    hist = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "assistant",
            "content": "FILE: a.py\n```python\n" + BODY_A.rstrip() + "\n```",
        },
    ]
    plan = _plan_full(["a.py", "b.py"])
    ctx, messages, check = _assemble(tmp_path, plan, hist)
    assert check.ok
    # a 可省但 messages 仍有 assistant FILE；b 必须在 user context
    vis = full_files_in_messages(messages)
    assert content_sha256(vis["a.py"]) == content_sha256(BODY_A)
    assert content_sha256(vis["b.py"]) == content_sha256(BODY_B)
    # user context 应含 b（或两者，若 b 非 omit）
    user = messages[-1]["content"]
    if "b.py" not in ctx.omitted_files:
        assert "--- FILE b.py" in user


# 阶段 B 强制：phase_a 错误 omit 时 revise
def test_t8b_presend_revise_forces_full(tmp_path):
    _ws(tmp_path, {"a.py": BODY_A})
    # 空历史 → phase_a 不应 omit；若强制 omit 则阶段 B 拉回
    hist = [{"role": "system", "content": SYSTEM_PROMPT}]
    proof = tracker_from_history(hist)
    plan = _plan_full(["a.py"])
    # 伪造 phase_a：直接标 omitted（模拟旧 bug）
    ctx = assemble_v12(tmp_path, plan, proof, load_arm("E"), record_context_marks=False)
    # 手动模拟错误 omit 后校验
    bad_omitted = ["a.py"]
    disk = {"a.py": content_sha256(BODY_A)}
    messages = build_messages(hist, "t", "[ctx] v1.2-E\n")  # 无 a.py
    check = verify_omissions_in_messages(messages, bad_omitted, disk)
    assert not check.ok
    assert check.missing_or_mismatch == ["a.py"]
    ctx2 = assemble_v12(
        tmp_path, plan, proof, load_arm("E"), force_full=set(check.missing_or_mismatch), record_context_marks=False
    )
    messages2 = build_messages(hist, "t", ctx2.text)
    check2 = verify_omissions_in_messages(messages2, list(ctx2.omitted_files), disk)
    assert check2.ok
    assert "--- FILE a.py" in messages2[-1]["content"]
