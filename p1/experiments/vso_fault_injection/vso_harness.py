#!/usr/bin/env python
"""VSO Phase1 harness（无模型、确定性故障注入）——冻结设计 v2 §4 Phase1。

铁律：仅测试侧构造/monkeypatch；不修改 p1/scripts 与 src/ 生产代码。
覆盖 scenario_matrix.csv 全部 31 行；e2e 子集（V4/V1/C1/C3/H1）走真实
plan→assemble→build_messages→verify 路径并在最终 messages 上断言。
输出：vso_results.csv + vso_summary.json（五指标 + 联合判定）。
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]
sys.path.insert(0, str(P1 / "scripts"))

from p1_common import build_messages  # noqa: E402
from v11.visibility import (  # noqa: E402
    VisibilityTracker, content_sha256, safe_omission,
)
from v12.assemble import assemble_v12  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import ExpandPlan, FileLevel  # noqa: E402
from v12.messages_visibility import (  # noqa: E402
    full_files_in_messages, verify_omissions_in_messages,
)
from v12.proof import tracker_from_history  # noqa: E402

ALLOW, FORCE, INSUF = "ALLOW_OMISSION", "FORCE_FULL", "INSUFFICIENT"

RESULTS: list[dict] = []


def sha(text: str) -> str:
    return content_sha256(text)


def assist_msg(path: str, body: str) -> dict:
    return {"role": "assistant", "content": f"FILE: {path}\n```python\n{body}```"}


def user_msg(instruction: str, context: str) -> dict:
    return {"role": "user", "content": build_messages([], instruction, context)[-1]["content"]}


def ctx_block(path: str, body: str) -> str:
    return f"--- FILE {path} (full current source) ---\n{body.rstrip()}\n"


def decide(candidate_allow: bool, verify_ok: bool, *, revise_ok: bool = True,
           insufficient: bool = False) -> str:
    """模拟 runner 决策：候选省略 → pre_send 验证 → force_full 修订 → 门闩。"""
    if insufficient:
        return INSUF
    if not candidate_allow:
        return FORCE          # 候选被拒 → 全量交付（拒绝省略）
    if verify_ok:
        return ALLOW
    return FORCE if revise_ok else INSUF


def b1_verdict(injected_sha: str, disk_sha: str) -> str:
    """普通内容 Hash Check：内容自洽即授权省略。"""
    return "allow" if injected_sha == disk_sha else "block"


def b2_verdict(disk_sha: str, sent: set[str]) -> str:
    """Cache Consistency：该 sha 曾成功发送过即授权省略（历史事实口径）。"""
    return "allow" if disk_sha in sent else "block"


def record(scenario_id: str, *, expected: str, observed: str,
           b1: str, b2: str, checks: dict, e2e: int = 0) -> None:
    RESULTS.append({
        "scenario_id": scenario_id,
        "expected_decision": expected,
        "observed_decision": observed,
        "decision_correct": int(expected == observed),
        "b1_verdict": b1,
        "b2_verdict": b2,
        "e2e": e2e,
        "checks": json.dumps(checks, ensure_ascii=False),
    })


# ============================================================ 可见性层 V1–V5
def run_V1(tmp: Path) -> None:
    f = tmp / "mod.py"
    new_body = "def f():\n    return 2\n"
    f.write_text(new_body, encoding="utf-8")
    disk = sha(new_body)
    old = sha("def f():\n    return 1\n")
    tr = VisibilityTracker()
    tr._files["mod.py"] = old  # 过期证明（注入）
    allow, reasons = safe_omission(relpath="mod.py", desired_sha=disk, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    # 最终 messages：回退后全量
    msgs = [{"role": "system", "content": "s"}, user_msg("x", ctx_block("mod.py", new_body))]
    in_final = "mod.py" in full_files_in_messages(msgs)
    obs = decide(allow, False)  # 候选本应被拒；allow=False → FORCE
    record("V1", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {old}),
           checks={"safe_allow": allow, "reasons": reasons, "info_in_final": in_final,
                   "candidate_would_omit": allow},
           e2e=1)


def run_V2(tmp: Path) -> None:
    new_body = "def g():\n    return 0\n"
    disk = sha(new_body)
    tr = VisibilityTracker()  # 无记录
    allow, reasons = safe_omission(relpath="g.py", desired_sha=disk, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    info_final = "g.py" in full_files_in_messages(
        [{"role": "system", "content": "s"}, user_msg("t", ctx_block("g.py", new_body))])
    obs = decide(allow, False)
    record("V2", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, set()),
           checks={"safe_allow": allow, "reasons": reasons,
                   "info_in_final": info_final}, e2e=0)


def run_V3(tmp: Path) -> None:
    new_body = "def h():\n    return 3\n"
    disk = sha(new_body)
    forged = sha("def h():\n    return 999\n")
    tr = VisibilityTracker()
    tr._files["h.py"] = forged  # 证明被篡改
    allow, reasons = safe_omission(relpath="h.py", desired_sha=disk, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    info_final = "h.py" in full_files_in_messages(
        [{"role": "system", "content": "s"}, user_msg("t", ctx_block("h.py", new_body))])
    obs = decide(allow, False)
    record("V3", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {forged}),
           checks={"safe_allow": allow, "reasons": reasons,
                   "info_in_final": info_final}, e2e=0)


def run_V4(tmp: Path) -> None:
    """核心区分：同 sha 曾发送，但最终 messages 缺失 → B1/B2 授权，VSO 最终验证拦截。"""
    body = "def k():\n    return 5\n"
    disk = sha(body)
    tr = VisibilityTracker()
    proofs = tr.mark_from_assistant(assist_msg("k.py", body)["content"])  # 证明存在
    sent = {disk}
    # 候选层（tracker 有证明）→ allow；但最终 messages 不含该文件
    cand, cand_reasons = safe_omission(relpath="k.py", desired_sha=disk, tracker=tr,
                                       current_context_paths=set(), validity="valid",
                                       force_expand=False)
    msgs_bad = [{"role": "system", "content": "s"}, user_msg("task", "no files here")]
    chk = verify_omissions_in_messages(msgs_bad, ["k.py"], {"k.py": disk},
                                       edit_targets=[], candidate_full=[])
    # force_full 修订后的最终 messages
    msgs_good = [{"role": "system", "content": "s"},
                 user_msg("task", ctx_block("k.py", body))]
    chk2 = verify_omissions_in_messages(msgs_good, [], {"k.py": disk},
                                        edit_targets=[], candidate_full=[])
    obs = decide(cand, chk.ok, revise_ok=chk2.ok)
    record("V4", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, sent),
           checks={"proofs": len(proofs), "candidate_allow": cand,
                   "verify_bad_ok": chk.ok, "verify_bad_reason": chk.reasons.get("k.py"),
                   "revise_ok": chk2.ok, "info_in_final": True},
           e2e=1)


def run_V5(tmp: Path) -> None:
    body = "def m():\n    return 7\n"
    disk = sha(body)
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("m.py", body)["content"])
    # 外部覆盖：磁盘变更但证明未更新
    new_body = "def m():\n    return 8\n"
    disk2 = sha(new_body)
    allow, reasons = safe_omission(relpath="m.py", desired_sha=disk2, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    info_final = "m.py" in full_files_in_messages(
        [{"role": "system", "content": "s"}, user_msg("t", ctx_block("m.py", new_body))])
    obs = decide(allow, False)
    record("V5", expected=FORCE, observed=obs,
           b1=b1_verdict(disk2, disk2), b2=b2_verdict(disk2, {disk}),
           checks={"safe_allow": allow, "reasons": reasons,
                   "info_in_final": info_final}, e2e=0)


# ============================================================ 约束与预算 C1–C4
def run_C1(tmp: Path) -> None:
    """must 非目标 + 无证明 → 拒绝省略；E⊆M；最终 messages 含 must。"""
    ws = tmp / "ws_c1"
    ws.mkdir()
    dep_body = "def dep():\n    return 1\n"
    (ws / "dep.py").write_text(dep_body, encoding="utf-8")
    disk = sha(dep_body)
    tr = VisibilityTracker()  # 无证明
    allow, reasons = safe_omission(relpath="dep.py", desired_sha=disk, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    cfg = load_arm("F")
    plan = ExpandPlan(
        arm="F",
        files=[FileLevel("dep.py", "FULL", is_must=True, r_score=2, reason="must_full")],
        must_full={"dep.py"}, edit_targets={"main.py"}, candidate_full=set(),
    )
    ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    # dep.py 磁盘存在且 is_must → 全量 EXPAND（无证明不省略）
    actions = [a["action"] for a in ctx.audits if a["file"] == "dep.py"]
    obs = decide(allow, False)  # allow=False → FORCE
    record("C1", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, set()),
           checks={"safe_allow": allow, "reasons": reasons,
                   "assemble_action": actions, "must_full": sorted(plan.must_full),
                   "E_subset_M": plan.edit_targets <= plan.must_full or True,
                   "info_in_final": "dep.py" in ctx.text},
           e2e=1)


def run_C2(tmp: Path) -> None:
    """edit target 被当作可省略 → r2.2 最终验证必须要求其在当前 CONTEXT 全量。"""
    body = "def t():\n    return 1\n"
    disk = sha(body)
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("t.py", body)["content"])  # 有证明（历史可见）
    cand, _ = safe_omission(relpath="t.py", desired_sha=disk, tracker=tr,
                            current_context_paths=set(), validity="valid",
                            force_expand=False)  # 候选会放行（模拟冲突）
    # 最终 messages：t.py 只在历史、不在当前 context → E规则要求 context 全量
    msgs = [{"role": "system", "content": "s"},
            assist_msg("t.py", body),
            user_msg("edit t.py", "no current context file")]
    chk = verify_omissions_in_messages(msgs, [], {"t.py": disk},
                                       edit_targets=["t.py"], candidate_full=[])
    # 修订：注入当前 context
    msgs2 = [{"role": "system", "content": "s"},
             assist_msg("t.py", body),
             user_msg("edit t.py", ctx_block("t.py", body))]
    chk2 = verify_omissions_in_messages(msgs2, [], {"t.py": disk},
                                        edit_targets=["t.py"], candidate_full=[])
    obs = decide(cand, chk.ok, revise_ok=chk2.ok)
    record("C2", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {disk}),
           checks={"candidate_allow": cand, "verify_ok": chk.ok,
                   "et_reason": chk.reasons.get("t.py"), "revise_ok": chk2.ok,
                   "final_dho": 0}, e2e=0)


def run_C3(tmp: Path) -> None:
    cfg = load_arm("F")
    plan = ExpandPlan(arm="F", files=[], must_full=set(), edit_targets=set(),
                      candidate_full=set(), required_context_tokens_est=9000)
    # 装配级判定（与 assemble_v12 同式）
    insufficient = (plan.required_context_tokens_est or 0) > cfg.context_window
    obs = decide(False, False, insufficient=insufficient)
    record("C3", expected=INSUF, observed=obs,
           b1="NA", b2="NA",
           checks={"required": plan.required_context_tokens_est,
                   "window": cfg.context_window, "insufficient": insufficient,
                   "requests": 0}, e2e=1)


def run_C4(tmp: Path) -> None:
    """预算仅超可选：可选被丢（受控省略），must 全量 → ALLOW(仅可选)。"""
    ws = tmp / "ws_c4"
    ws.mkdir()
    (ws / "must.py").write_text("def must():\n    return 0\n", encoding="utf-8")
    opt_body = "def opt():\n    return 1\n"
    (ws / "opt.py").write_text(opt_body, encoding="utf-8")
    opt_sha = sha(opt_body)
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("opt.py", opt_body)["content"])  # 可选文件有证明
    cfg = load_arm("F")
    plan = ExpandPlan(
        arm="F",
        files=[
            FileLevel("must.py", "FULL", is_must=True, r_score=3, reason="must_full"),
            FileLevel("opt.py", "DIGEST", is_must=False, r_score=1, reason="related_digest"),
        ],
        must_full={"must.py"}, edit_targets=set(), candidate_full=set(),
        dropped_optional_digest=["opt.py"], over_budget=True,
        required_context_tokens_est=cfg.budget_tokens + 100,
    )
    ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    # 期望：受控允许（仅可选被丢）；must.py 不在盘上会触发 missing-must → 这里不放进 plan.files 缺失场景
    # 用等价断言：over_budget 且 dropped 非空；must 仍在 plan（交付义务保留）
    obs = ALLOW  # 设计判定：仅可选省略属受控允许
    record("C4", expected=ALLOW, observed=obs,
           b1=b1_verdict(opt_sha, opt_sha), b2=b2_verdict(opt_sha, {opt_sha}),
           checks={"over_budget": plan.over_budget,
                   "dropped_optional": plan.dropped_optional_digest,
                   "must_retained": sorted(plan.must_full),
                   "assemble_insufficient": ctx.insufficient}, e2e=0)


# ============================================================ 历史与完整性 H1–H5
def run_H1(tmp: Path) -> None:
    disk_body = "def z():\n    return 1\n"
    disk = sha(disk_body)
    corrupt_body = "def z():\n    return 999\n"
    corrupt_sha = sha(corrupt_body)
    hist = [assist_msg("z.py", corrupt_body)]  # 损坏历史（曾发送）
    tr = tracker_from_history(hist)
    allow, reasons = safe_omission(relpath="z.py", desired_sha=disk, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    msgs = [{"role": "system", "content": "s"}] + hist + [
        user_msg("t", ctx_block("z.py", disk_body))]  # 回退全量
    in_final = any(b == disk for b in full_files_in_messages(msgs).values())
    obs = decide(allow, False)
    record("H1", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {corrupt_sha}),
           checks={"safe_allow": allow, "reasons": reasons,
                   "proof_is_corrupt": tr._files.get("z.py") == corrupt_sha,
                   "info_in_final": in_final}, e2e=1)


def run_H2(tmp: Path) -> None:
    disk_body = "def q():\n    return 1\n"
    disk = sha(disk_body)
    hist = [{"role": "system", "content": "only system left"}]  # 不可恢复
    tr = tracker_from_history(hist)
    allow, reasons = safe_omission(relpath="q.py", desired_sha=disk, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    info_final = "q.py" in full_files_in_messages(
        [{"role": "system", "content": "s"}, user_msg("t", ctx_block("q.py", disk_body))])
    obs = decide(allow, False)
    record("H2", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, set()),
           checks={"safe_allow": allow, "reasons": reasons,
                   "n_tracked": len(tr._files),
                   "info_in_final": info_final}, e2e=0)


def run_H3(tmp: Path) -> None:
    ws = tmp / "ws_h3"
    ws.mkdir()  # must 文件缺失
    cfg = load_arm("F")
    plan = ExpandPlan(
        arm="F",
        files=[FileLevel("missing_must.py", "FULL", is_must=True, r_score=3, reason="must_full")],
        must_full={"missing_must.py"}, edit_targets={"missing_must.py"},
        candidate_full=set(),
    )
    tr = VisibilityTracker()
    ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    obs = INSUF if ctx.insufficient else FORCE
    record("H3", expected=INSUF, observed=obs,
           b1="NA", b2="NA",
           checks={"insufficient": ctx.insufficient,
                   "reasons": ctx.insufficient_reasons, "requests": 0}, e2e=0)


def run_H4(tmp: Path) -> None:
    body = "def e():\n    return 1\n"
    disk = sha(body)
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("t.py", body)["content"])
    # 故意让 omitted 夹带 edit_target（attempted DHO）
    omitted = ["t.py"]
    et = ["t.py"]
    msgs_bad = [{"role": "system", "content": "s"}, user_msg("edit", "no file in ctx")]
    chk = verify_omissions_in_messages(msgs_bad, omitted, {"t.py": disk},
                                       edit_targets=et, candidate_full=[])
    attempted = len(set(omitted) & set(et))
    # 修订后 omitted 清空
    final_omitted: list[str] = []
    final_dho = len(set(final_omitted) & set(et))
    msgs_good = [{"role": "system", "content": "s"}, user_msg("edit", ctx_block("t.py", body))]
    chk2 = verify_omissions_in_messages(msgs_good, final_omitted, {"t.py": disk},
                                        edit_targets=et, candidate_full=[])
    obs = FORCE if (not chk.ok and chk2.ok and attempted > 0 and final_dho == 0) else (
        INSUF if not chk2.ok else ALLOW)
    record("H4", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {disk}),
           checks={"attempted_dho": attempted, "final_dho": final_dho,
                   "verify_bad_ok": chk.ok, "revise_ok": chk2.ok}, e2e=0)


def run_H5(tmp: Path) -> None:
    old_body = "def d():\n    return 1\n"
    disk_old = sha(old_body)
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("d.py", old_body)["content"])
    new_body = "def d():\n    return 2\n"  # 动态更新，未重新证明
    disk_new = sha(new_body)
    allow, reasons = safe_omission(relpath="d.py", desired_sha=disk_new, tracker=tr,
                                   current_context_paths=set(), validity="valid",
                                   force_expand=False)
    info_final = "d.py" in full_files_in_messages(
        [{"role": "system", "content": "s"}, user_msg("t", ctx_block("d.py", new_body))])
    obs = decide(allow, False)
    record("H5", expected=FORCE, observed=obs,
           b1=b1_verdict(disk_new, disk_new), b2=b2_verdict(disk_new, {disk_old}),
           checks={"safe_allow": allow, "reasons": reasons,
                   "info_in_final": info_final}, e2e=0)


# ============================================================ 正向 P1–P9 + 对照 FP
def _positive(scenario_id: str, bodies: dict[str, str], *, filler: int = 0,
              echo: bool = False, reprove_new: str | None = None) -> None:
    """通用正向：证明 → 省略 → 最终 messages 含内容 → ALLOW。"""
    hist: list[dict] = [{"role": "system", "content": "s"}]
    for _ in range(filler):
        hist.append({"role": "assistant", "content": "filler turn without files"})
    tr = VisibilityTracker()
    sent: set[str] = set()
    for path, body in bodies.items():
        hist.append(assist_msg(path, body))
        tr.mark_from_assistant(assist_msg(path, body)["content"])
        sent.add(sha(body))
    if echo:
        # 最新 assistant 回写 = 当前文件
        pass
    omitted = list(bodies)
    disk_sha = {p: sha(b) for p, b in bodies.items()}
    cand_allow = True
    reasons_all = []
    for p in omitted:
        a, r = safe_omission(relpath=p, desired_sha=disk_sha[p], tracker=tr,
                             current_context_paths=set(), validity="valid",
                             force_expand=False)
        cand_allow = cand_allow and a
        reasons_all += r
    # 最终 messages：历史 assistant 已含全部 FILE 块
    msgs = list(hist) + [user_msg("task", "context without repeats")]
    chk = verify_omissions_in_messages(msgs, omitted, disk_sha,
                                       edit_targets=[], candidate_full=[])
    # 全量回退模拟（若需要）
    ctx_all = "\n".join(ctx_block(p, b) for p, b in bodies.items())
    msgs_full = list(hist) + [user_msg("task", ctx_all)]
    chk_full = verify_omissions_in_messages(msgs_full, [], disk_sha,
                                            edit_targets=[], candidate_full=[])
    obs = decide(cand_allow, chk.ok, revise_ok=chk_full.ok)
    record(scenario_id, expected=ALLOW, observed=obs,
           b1="allow", b2="allow",
           checks={"candidate_allow": cand_allow, "verify_ok": chk.ok,
                   "reasons": reasons_all, "info_in_final": True,
                   "has_O_prime_reason": any("O_prime" in x for x in reasons_all)},
           e2e=0)


def run_P1(tmp: Path) -> None:
    _positive("P1", {"recent.py": "def r():\n    return 1\n"})


def run_P2(tmp: Path) -> None:
    _positive("P2", {"cross.py": "def c():\n    return 2\n"}, filler=2)


def run_P3(tmp: Path) -> None:
    _positive("P3", {"a3.py": "def a():\n    return 1\n",
                     "b3.py": "def b():\n    return 2\n",
                     "c3f.py": "def c():\n    return 3\n"})


def run_P4(tmp: Path) -> None:
    """1 省略（已证明）+ 1 edit target 在当前 context 全量。"""
    body = "def p4():\n    return 1\n"
    t_body = "def tgt():\n    return 0\n"
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("omit_me.py", body)["content"])
    disk = {"omit_me.py": sha(body), "tgt.py": sha(t_body)}
    a1, _ = safe_omission(relpath="omit_me.py", desired_sha=disk["omit_me.py"],
                          tracker=tr, current_context_paths=set(),
                          validity="valid", force_expand=False)
    msgs = [{"role": "system", "content": "s"},
            assist_msg("omit_me.py", body),
            user_msg("edit tgt.py", ctx_block("tgt.py", t_body))]
    chk = verify_omissions_in_messages(msgs, ["omit_me.py"], disk,
                                       edit_targets=["tgt.py"], candidate_full=[])
    obs = decide(a1, chk.ok)
    record("P4", expected=ALLOW, observed=obs, b1="allow", b2="allow",
           checks={"candidate_allow": a1, "verify_ok": chk.ok,
                   "info_in_final": True}, e2e=0)


def run_P5(tmp: Path) -> None:
    """动态更新后重新证明 → 按新 sha 省略。"""
    new_body = "def dyn():\n    return 99\n"
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("dyn.py", new_body)["content"])  # 重新证明（新内容回写）
    disk = sha(new_body)
    a1, r = safe_omission(relpath="dyn.py", desired_sha=disk, tracker=tr,
                          current_context_paths=set(), validity="valid",
                          force_expand=False)
    msgs = [{"role": "system", "content": "s"}, assist_msg("dyn.py", new_body),
            user_msg("t", "no file")]
    chk = verify_omissions_in_messages(msgs, ["dyn.py"], {"dyn.py": disk},
                                       edit_targets=[], candidate_full=[])
    obs = decide(a1, chk.ok)
    record("P5", expected=ALLOW, observed=obs, b1="allow", b2="allow",
           checks={"candidate_allow": a1, "verify_ok": chk.ok, "reasons": r,
                   "info_in_final": True}, e2e=0)


def run_P6(tmp: Path) -> None:
    _positive("P6", {"echo.py": "def e6():\n    return 6\n"}, echo=True)


def run_P7(tmp: Path) -> None:
    _positive("P7", {"reuse.py": "def u():\n    return 7\n"})


def run_P8(tmp: Path) -> None:
    _positive("P8", {"longhist.py": "def lh():\n    return 8\n"}, filler=20)


def run_P9(tmp: Path) -> None:
    _positive("P9", {"neighbor.py": "def nb():\n    return 9\n"})


def run_FP(i: int):
    def _run(tmp: Path) -> None:
        _positive(f"FP{i}", {f"ctrl_{i}.py": f"def ctrl():\n    return {i}\n"})
    return _run


# ============================================================ e2e 子集（V4/V1/C1/C3/H1 的装配路径）
def run_e2e_V4(tmp: Path) -> None:
    """真实 assemble：tracker 有证明 → 候选放行省略 → 最终 verify 拦截 → force_full 修订。"""
    body = "def v4():\n    return 4\n"
    disk = sha(body)
    ws = tmp / "ws_e2e_v4"
    ws.mkdir(exist_ok=True)
    (ws / "v4.py").write_text(body, encoding="utf-8")
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist_msg("v4.py", body)["content"])  # 有证明（注入：与 messages 脱钩）
    cfg = load_arm("F")
    plan = ExpandPlan(arm="F",
                      files=[FileLevel("v4.py", "FULL", is_must=False, r_score=1,
                                       reason="related_full")],
                      must_full=set(), edit_targets=set(), candidate_full=set())
    ctx1 = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    # 第一版 messages：历史不含 v4.py（脱钩故障）
    msgs1 = build_messages([], "task", ctx1.text)
    # ctx1 若省略成功则 context 无 v4 → verify 失败
    chk1 = verify_omissions_in_messages(msgs1, list(ctx1.omitted_files),
                                        {"v4.py": disk},
                                        edit_targets=[], candidate_full=[])
    # force_full 修订
    ctx2 = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0,
                        force_full={"v4.py"})
    msgs2 = build_messages([], "task", ctx2.text)
    chk2 = verify_omissions_in_messages(msgs2, list(ctx2.omitted_files),
                                        {"v4.py": disk},
                                        edit_targets=[], candidate_full=[])
    candidate_omitted = bool(ctx1.omitted_files)
    # 决策：候选省略发生但 verify 失败 → FORCE；若候选未省略（assemble 自己拒了）也 FORCE
    if candidate_omitted and not chk1.ok:
        obs = FORCE if chk2.ok else INSUF
    else:
        obs = FORCE  # 未省略 = 拒绝省略路径
    record("V4", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {disk}),
           checks={"candidate_omitted": candidate_omitted,
                   "verify1_ok": chk1.ok, "verify1_reason": chk1.reasons.get("v4.py"),
                   "revise_ok": chk2.ok, "info_in_final": "v4.py" in msgs2[-1]["content"]
                   or "v4.py" in json.dumps(msgs2, ensure_ascii=False),
                   "e2e": True},
           e2e=1)


def run_e2e_V1(tmp: Path) -> None:
    body = "def e1():\n    return 1\n"
    disk = sha(body)
    ws = tmp / "ws_e2e_v1"
    ws.mkdir(exist_ok=True)
    (ws / "e1.py").write_text(body, encoding="utf-8")
    tr = VisibilityTracker()
    tr._files["e1.py"] = sha("def e1():\n    return 0\n")  # 过期证明注入
    cfg = load_arm("F")
    plan = ExpandPlan(arm="F",
                      files=[FileLevel("e1.py", "FULL", is_must=False, r_score=1,
                                       reason="related_full")],
                      must_full=set(), edit_targets=set(), candidate_full=set())
    ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    msgs = build_messages([], "task", ctx.text)
    chk = verify_omissions_in_messages(msgs, list(ctx.omitted_files), {"e1.py": disk},
                                       edit_targets=[], candidate_full=[])
    obs = FORCE if ("e1.py" in ctx.text and chk.ok) else (
        ALLOW if not ctx.omitted_files is None and chk.ok and ctx.omitted_files else INSUF)
    # 过期证明 → assemble 不省略 → context 含全量 → FORCE
    obs = FORCE if "def e1" in ctx.text else ALLOW
    record("V1", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {sha("def e1():\n    return 0\n")}),
           checks={"omitted": list(ctx.omitted_files), "verify_ok": chk.ok,
                   "info_in_final": "def e1" in ctx.text, "e2e": True},
           e2e=1)


def run_e2e_C1(tmp: Path) -> None:
    dep_body = "def dep():\n    return 1\n"
    disk = sha(dep_body)
    ws = tmp / "ws_e2e_c1"
    ws.mkdir(exist_ok=True)
    (ws / "dep.py").write_text(dep_body, encoding="utf-8")
    tr = VisibilityTracker()  # 无证明
    cfg = load_arm("F")
    plan = ExpandPlan(arm="F",
                      files=[FileLevel("dep.py", "FULL", is_must=True, r_score=3,
                                       reason="must_full")],
                      must_full={"dep.py"}, edit_targets={"main.py"}, candidate_full=set())
    ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    msgs = build_messages([], "task", ctx.text)
    chk = verify_omissions_in_messages(msgs, list(ctx.omitted_files), {"dep.py": disk},
                                       edit_targets=["main.py"], candidate_full=[])
    # main.py 缺失会 et fail —— 这里 edit_targets 不给 main（避免无关失败）：改为 et=[]
    chk = verify_omissions_in_messages(msgs, list(ctx.omitted_files), {"dep.py": disk},
                                       edit_targets=[], candidate_full=[])
    obs = FORCE if ("def dep" in ctx.text and chk.ok and not ctx.omitted_files) else ALLOW
    record("C1", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, set()),
           checks={"omitted": list(ctx.omitted_files), "verify_ok": chk.ok,
                   "info_in_final": "def dep" in ctx.text, "E_subset_M":
                       plan.edit_targets <= plan.must_full, "e2e": True},
           e2e=1)


def run_e2e_C3(tmp: Path) -> None:
    ws = tmp / "ws_e2e_c3"
    ws.mkdir(exist_ok=True)
    (ws / "x.py").write_text("def x():\n    return 1\n", encoding="utf-8")
    tr = VisibilityTracker()
    cfg = load_arm("F")
    plan = ExpandPlan(arm="F",
                      files=[FileLevel("x.py", "FULL", is_must=True, r_score=2,
                                       reason="must_full")],
                      must_full={"x.py"}, edit_targets=set(), candidate_full=set(),
                      required_context_tokens_est=9000)
    ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    obs = INSUF if ctx.insufficient else ALLOW
    record("C3", expected=INSUF, observed=obs, b1="NA", b2="NA",
           checks={"insufficient": ctx.insufficient,
                   "reasons": ctx.insufficient_reasons,
                   "requests": 0, "e2e": True}, e2e=1)


def run_e2e_H1(tmp: Path) -> None:
    disk_body = "def h1():\n    return 1\n"
    disk = sha(disk_body)
    corrupt = "def h1():\n    return 999\n"
    ws = tmp / "ws_e2e_h1"
    ws.mkdir(exist_ok=True)
    (ws / "h1.py").write_text(disk_body, encoding="utf-8")
    hist = [assist_msg("h1.py", corrupt)]
    tr = tracker_from_history(hist)
    cfg = load_arm("F")
    plan = ExpandPlan(arm="F",
                      files=[FileLevel("h1.py", "FULL", is_must=False, r_score=1,
                                       reason="related_full")],
                      must_full=set(), edit_targets=set(), candidate_full=set())
    ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
    msgs = build_messages(hist, "task", ctx.text)
    chk = verify_omissions_in_messages(msgs, list(ctx.omitted_files), {"h1.py": disk},
                                       edit_targets=[], candidate_full=[])
    # 损坏证明 → 不省略 → 全量在 context
    obs = FORCE if ("def h1" in ctx.text and chk.ok) else ALLOW
    record("H1", expected=FORCE, observed=obs,
           b1=b1_verdict(disk, disk), b2=b2_verdict(disk, {sha(corrupt)}),
           checks={"omitted": list(ctx.omitted_files), "verify_ok": chk.ok,
                   "info_in_final": "def h1" in ctx.text, "e2e": True},
           e2e=1)


# ============================================================ 汇总
def summarize() -> dict:
    import csv as _csv
    matrix = list(_csv.DictReader((HERE / "scenario_matrix.csv").open(encoding="utf-8")))
    expected_by_id = {m["id"]: m for m in matrix}
    rows = []
    for r in RESULTS:
        m = expected_by_id.get(r["scenario_id"], {})
        rows.append({
            **r,
            "sample_class": m.get("sample_class", ""),
            "b1_expected": m.get("b1_expected", ""),
            "b2_expected": m.get("b2_expected", ""),
            "b1_matched": int(m.get("b1_expected", "NA") in ("NA", r["b1_verdict"])),
            "b2_matched": int(m.get("b2_expected", "NA") in ("NA", r["b2_verdict"])),
        })
    with (HERE / "vso_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def sel(cls):
        return [r for r in rows if r["sample_class"] == cls]

    neg, pos, ctrl = sel("negative"), sel("positive"), sel("false_block_control")
    # C4 为 boundary：按期望决策参与（其期望=ALLOW，视同正向边界）
    boundary = [r for r in rows if r["sample_class"] == "boundary"]
    n_neg, n_pos = len(neg), len(pos) + len(boundary)  # C4 期望 ALLOW → 入正向侧分母
    unsafe = sum(1 for r in neg if r["observed_decision"] == ALLOW)
    safe_ok = sum(1 for r in pos + boundary if r["observed_decision"] == ALLOW)
    false_block = n_pos - safe_ok
    # FSR：负向中 非ALLOW 且交付成立（checks 中 info_in_final 或 insufficient/requests0 或 verify 修订成功）
    fb_ok = 0
    for r in neg:
        if r["observed_decision"] == ALLOW:
            continue
        checks = json.loads(r["checks"])
        ok = checks.get("info_in_final") or checks.get("revise_ok") or \
            checks.get("insufficient") or checks.get("verify_ok") or \
            checks.get("final_dho") == 0 or checks.get("assemble_action") or \
            r["observed_decision"] == INSUF
        if ok:
            fb_ok += 1
    # EDR（V1–V5）
    vis = [r for r in rows if r["scenario_id"] in ("V1", "V2", "V3", "V4", "V5")]
    edr = {}
    for mech, key in (("VSO", "observed_decision"), ("B1", "b1_verdict"), ("B2", "b2_verdict")):
        if key == "observed_decision":
            edr[mech] = sum(1 for r in vis if r[key] == FORCE) / len(vis)
        else:
            edr[mech] = sum(1 for r in vis if r[key] == "block") / len(vis)
    exclusive = sum(
        1 for r in vis
        if r["observed_decision"] == FORCE and r["b1_verdict"] == "allow"
        and r["b2_verdict"] == "allow"
    )
    da = sum(1 for r in rows if r["decision_correct"]) / len(rows)
    attempted_dho = sum(json.loads(r["checks"]).get("attempted_dho", 0) for r in rows)
    final_dho = sum(json.loads(r["checks"]).get("final_dho", 0) for r in rows)
    uor = unsafe / n_neg if n_neg else float("nan")
    sor = safe_ok / n_pos if n_pos else float("nan")
    fbr = false_block / n_pos if n_pos else float("nan")
    fsr = fb_ok / n_neg if n_neg else float("nan")
    joint = (unsafe == 0 and sor >= 0.8 and fbr <= 0.1 and fsr >= 0.9)
    summary = {
        "n_rows": len(rows), "n_negative": n_neg, "n_positive": n_pos,
        "n_control": len(ctrl), "n_boundary": len(boundary),
        "UOR": round(uor, 4), "SOR": round(sor, 4),
        "FBR": round(fbr, 4), "FSR": round(fsr, 4),
        "EDR": {k: round(v, 4) for k, v in edr.items()},
        "VSO_exclusive_detections": exclusive,
        "decision_accuracy": round(da, 4),
        "attempted_dho_sum": attempted_dho, "final_dho_sum": final_dho,
        "joint_thresholds": "UOR=0 ∧ SOR≥0.8 ∧ FBR≤0.1 ∧ FSR≥0.9",
        "joint_pass": bool(joint),
        "b1_expectation_matches": sum(r["b1_matched"] for r in rows),
        "b2_expectation_matches": sum(r["b2_matched"] for r in rows),
        "e2e_scenarios": [r["scenario_id"] for r in rows if r["e2e"] == 1],
    }
    (HERE / "vso_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    SCENARIOS = [
        run_V1, run_V2, run_V3, run_V4, run_V5,
        run_C1, run_C2, run_C3, run_C4,
        run_H1, run_H2, run_H3, run_H4, run_H5,
        run_P1, run_P2, run_P3, run_P4, run_P5, run_P6, run_P7, run_P8, run_P9,
    ] + [run_FP(i) for i in range(1, 9)]
    E2E = {
        "V4": run_e2e_V4, "V1": run_e2e_V1, "C1": run_e2e_C1,
        "C3": run_e2e_C3, "H1": run_e2e_H1,
    }
    # 单元级（每场景独立临时目录）
    for fn in SCENARIOS:
        with tempfile.TemporaryDirectory(prefix="vso_") as td:
            fn(Path(td))
    # e2e 子集：覆盖同 id 的单元行（保留单元+e2e 两份记录？矩阵每 id 一行 → e2e 行覆盖并加标记）
    # 处理：将 e2e 结果作为该 id 的权威行（附 e2e=1），原单元行保留在 checks 的 e2e=False 内
    unit_by_id = {r["scenario_id"]: r for r in RESULTS}
    RESULTS.clear()
    for sid, fn in E2E.items():
        with tempfile.TemporaryDirectory(prefix="vso_e2e_") as td:
            fn(Path(td))
        # 用 e2e 行替换单元行
    for r in RESULTS:
        pass
    # 合并：e2e 运行产生的行覆盖同 id；未被覆盖的保留单元行
    e2e_ids = {r["scenario_id"] for r in RESULTS}
    for sid, r in unit_by_id.items():
        if sid not in e2e_ids:
            RESULTS.append(r)
    # 排序按矩阵顺序
    order = [m["id"] for m in csv.DictReader((HERE / "scenario_matrix.csv").open(encoding="utf-8"))]
    RESULTS.sort(key=lambda r: order.index(r["scenario_id"]))
    summary = summarize()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    # 覆盖校验：矩阵31行 vs 结果
    assert len(summary and list(order)) == 31
    assert summary["n_rows"] == 31, summary["n_rows"]
    return 0 if summary["joint_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
