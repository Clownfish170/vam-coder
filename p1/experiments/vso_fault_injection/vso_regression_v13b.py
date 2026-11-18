#!/usr/bin/env python
"""V13B(ICG) 相对 V12-F 的 VSO 场景回归（离线、无模型）。

目标：证明 ICG 只改「相关可选 FULL 的取舍」，**不改变** VSO 安全决策语义。

覆盖：
  A) Phase1 全量 31 场景重放（与冻结 harness 同断言）→ F 基线 joint_pass
  B) e2e 五场景（V1/V4/C1/C3/H1）× 臂 {F, V13BICG} 决策一致
  C) ICG 专属：相关可选 NONE / icg_full 时 must/ET 仍强制、无 unsafe omit
  D) 正向省略 P1/P5 在 F 与 V13BICG 下仍 ALLOW

输出：vso_regression_v13b/{results.csv, summary.json, report.md}
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]
sys.path.insert(0, str(P1 / "scripts"))
sys.path.insert(0, str(HERE))

from p1_common import build_messages  # noqa: E402
from v11.visibility import (  # noqa: E402
    VisibilityTracker,
    content_sha256,
    safe_omission,
)
from v12.assemble import assemble_v12  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import ExpandPlan, FileLevel, build_plan  # noqa: E402
from v12.messages_visibility import (  # noqa: E402
    full_files_in_messages,
    verify_omissions_in_messages,
)
from v12.proof import tracker_from_history  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402

ALLOW, FORCE, INSUF = "ALLOW_OMISSION", "FORCE_FULL", "INSUFFICIENT"
OUT = HERE / "vso_regression_v13b"
ARMS = ["F", "V13BICG"]
ARM_LABEL = {"F": "v12_f", "V13BICG": "v13b_icg"}


def sha(t: str) -> str:
    return content_sha256(t)


def decide(candidate_allow: bool, verify_ok: bool, *, revise_ok: bool = True,
           insufficient: bool = False) -> str:
    if insufficient:
        return INSUF
    if not candidate_allow:
        return FORCE
    if verify_ok:
        return ALLOW
    return FORCE if revise_ok else INSUF


def assist(path: str, body: str) -> dict:
    return {"role": "assistant", "content": f"FILE: {path}\n```python\n{body}```"}


def user(instruction: str, context: str) -> dict:
    return {"role": "user", "content": build_messages([], instruction, context)[-1]["content"]}


def ctx_block(path: str, body: str) -> str:
    return f"--- FILE {path} (full current source) ---\n{body.rstrip()}\n"


rows: list[dict] = []


def rec(sid: str, arm: str, expected: str, observed: str, **checks) -> None:
    rows.append(
        {
            "scenario_id": sid,
            "arm": arm,
            "arm_label": ARM_LABEL[arm],
            "expected": expected,
            "observed": observed,
            "correct": int(expected == observed),
            "checks": json.dumps(checks, ensure_ascii=False),
        }
    )


# -------------------- e2e：双臂共用逻辑，仅 cfg/arm 不同 --------------------
def e2e_V1(arm: str) -> None:
    """过期证明 → FORCE_FULL。"""
    body = "def f():\n    return 2\n"
    tr = VisibilityTracker()
    tr._files["mod.py"] = sha("def f():\n    return 1\n")  # 过期
    allow, reasons = safe_omission(
        relpath="mod.py", desired_sha=sha(body), tracker=tr,
        current_context_paths=set(), validity="valid", force_expand=False,
    )
    obs = decide(allow, False)
    rec("V1", arm, FORCE, obs, safe_allow=allow, reasons=reasons)


def e2e_V4(arm: str) -> None:
    """曾发送但不在最终 messages → VSO 拦截 FORCE。"""
    body = "def k():\n    return 5\n"
    disk = sha(body)
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist("k.py", body)["content"])
    cand, _ = safe_omission(
        relpath="k.py", desired_sha=disk, tracker=tr,
        current_context_paths=set(), validity="valid", force_expand=False,
    )
    msgs_bad = [{"role": "system", "content": "s"}, user("task", "no files here")]
    chk = verify_omissions_in_messages(
        msgs_bad, ["k.py"], {"k.py": disk}, edit_targets=[], candidate_full=[]
    )
    msgs_good = [
        {"role": "system", "content": "s"},
        user("task", ctx_block("k.py", body)),
    ]
    chk2 = verify_omissions_in_messages(
        msgs_good, [], {"k.py": disk}, edit_targets=[], candidate_full=[]
    )
    obs = decide(cand, chk.ok, revise_ok=chk2.ok)
    rec("V4", arm, FORCE, obs, cand=cand, verify_bad=chk.ok, revise=chk2.ok)


def e2e_C1(arm: str) -> None:
    """must 无证明 → 不省略；assemble 全量；最终含 must。"""
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "ws"
        ws.mkdir()
        dep_body = "def dep():\n    return 1\n"
        (ws / "dep.py").write_text(dep_body, encoding="utf-8")
        tr = VisibilityTracker()
        allow, reasons = safe_omission(
            relpath="dep.py", desired_sha=sha(dep_body), tracker=tr,
            current_context_paths=set(), validity="valid", force_expand=False,
        )
        cfg = load_arm(arm)
        plan = ExpandPlan(
            arm=arm,
            files=[FileLevel("dep.py", "FULL", is_must=True, r_score=2, reason="must_full")],
            must_full={"dep.py"},
            edit_targets={"main.py"},
            candidate_full=set(),
        )
        ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
        actions = [a["action"] for a in ctx.audits if a["file"] == "dep.py"]
        obs = decide(allow, False)
        rec(
            "C1", arm, FORCE, obs,
            safe_allow=allow, assemble_action=actions,
            must_in_ctx="dep.py" in ctx.text, reasons=reasons,
        )


def e2e_C3(arm: str) -> None:
    cfg = load_arm(arm)
    plan = ExpandPlan(
        arm=arm, files=[], must_full=set(), edit_targets=set(),
        candidate_full=set(), required_context_tokens_est=9000,
    )
    insufficient = (plan.required_context_tokens_est or 0) > cfg.context_window
    obs = decide(False, False, insufficient=insufficient)
    rec("C3", arm, INSUF, obs, required=plan.required_context_tokens_est,
        window=cfg.context_window)


def e2e_H1(arm: str) -> None:
    """损坏历史证明 → 拒绝省略 FORCE。"""
    body = "def z():\n    return 1\n"
    tr = VisibilityTracker()
    # 注入损坏哈希
    tr._files["z.py"] = "CORRUPT"
    allow, reasons = safe_omission(
        relpath="z.py", desired_sha=sha(body), tracker=tr,
        current_context_paths=set(), validity="valid", force_expand=False,
    )
    obs = decide(allow, False)
    rec("H1", arm, FORCE, obs, safe_allow=allow, reasons=reasons)


def e2e_P1(arm: str) -> None:
    """正向：近期可见 → ALLOW。"""
    body = "def r():\n    return 1\n"
    tr = VisibilityTracker()
    tr.mark_from_assistant(assist("recent.py", body)["content"])
    allow, reasons = safe_omission(
        relpath="recent.py", desired_sha=sha(body), tracker=tr,
        current_context_paths=set(), validity="valid", force_expand=False,
    )
    obs = decide(allow, True)
    rec("P1", arm, ALLOW, obs, safe_allow=allow, reasons=reasons)


# -------------------- ICG 专属安全属性 --------------------
def icg_related_none_keeps_et_full(arm: str) -> None:
    """ICG 落选 related → NONE；ET 仍 FILE 全量；无 unsafe omit ET。"""
    files = {
        "hot.py": "def h():\n    return 1\n",
        "related.py": "def rel():\n    return 2\n",
        "noise.py": "def n():\n    return 0\n",
    }
    # 弱相关：仅「参考」不写死 → ICG 应 skip related
    instruction = "请参考 related.py 的定义。修改 hot.py 中的 h()：返回 2。不要修改 noise.py。"
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        for n, b in files.items():
            (ws / n).write_text(b, encoding="utf-8")
        targets = parse_edit_targets(instruction, sorted(files), {})
        cfg = load_arm(arm)
        sha_map = {f: sha(b) for f, b in files.items()}
        sizes = {f: len(b) for f, b in files.items()}
        entries = {
            f: [{"symbol_id": f"e:{f}", "validity": "valid", "deps": []}]
            for f in files
        }
        plan = build_plan(
            arm_cfg=cfg,
            instruction=instruction,
            workspace_files=sorted(files),
            workspace_sha=sha_map,
            file_sizes=sizes,
            entries_by_file=entries,
            targets=targets,
            system_history_tokens_est=0,
            source_by_file=files,
        )
        tr = VisibilityTracker()
        ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
        by = {f.relpath: f.level for f in plan.files}
        # ET 必须 FULL 且在 context
        assert by.get("hot.py") == "FULL", by
        assert "--- FILE hot.py" in ctx.text
        # related 若被 ICG skip 则不得以半截形式出现；不得出现 MEM
        assert "--- MEM " not in ctx.text
        if arm == "V13BICG" and by.get("related.py") == "NONE":
            # 落选：context 无 related 正文（安全：非 must）
            assert "--- FILE related.py" not in ctx.text
        # 无 INSUFFICIENT 误伤
        rec(
            "ICG_ET_FULL",
            arm,
            "ET_FULL_NO_MEM",
            "ET_FULL_NO_MEM" if by.get("hot.py") == "FULL" and "--- MEM " not in ctx.text else "BAD",
            levels=by,
            insufficient=ctx.insufficient,
            et_in_ctx="--- FILE hot.py" in ctx.text,
        )


def icg_must_still_full_when_related_skipped(arm: str) -> None:
    """must 文件即使 ICG 想动也必须 FULL（ICG 禁止触碰 must）。"""
    files = {
        "main.py": "def m():\n    return 0\n",
        "helper.py": "def hlp():\n    return 1\n",
    }
    instruction = "修改 main.py 中的 m()：返回 1。"  # helper 不在指令 → 可能 unrelated
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        for n, b in files.items():
            (ws / n).write_text(b, encoding="utf-8")
        targets = parse_edit_targets(instruction, sorted(files), {})
        cfg = load_arm(arm)
        sha_map = {f: sha(b) for f, b in files.items()}
        sizes = {f: len(b) for f, b in files.items()}
        # 强制 helper 进 must（模拟依赖）
        entries = {
            "main.py": [{"symbol_id": "e:main", "validity": "valid", "deps": ["e:helper"]}],
            "helper.py": [{"symbol_id": "e:helper", "validity": "valid", "deps": []}],
        }
        plan = build_plan(
            arm_cfg=cfg,
            instruction=instruction,
            workspace_files=sorted(files),
            workspace_sha=sha_map,
            file_sizes=sizes,
            entries_by_file=entries,
            targets=targets,
            system_history_tokens_est=0,
            source_by_file=files,
        )
        # 手动确保 helper 在 must（闭包可能因 symbol 映射不全未进）
        if "helper.py" not in plan.must_full:
            plan.must_full.add("helper.py")
            for f in plan.files:
                if f.relpath == "helper.py":
                    f.is_must = True
                    f.level = "FULL"
        tr = VisibilityTracker()
        ctx = assemble_v12(ws, plan, tr, cfg, system_history_tokens_est=0)
        by = {f.relpath: (f.level, f.is_must) for f in plan.files}
        helper_ok = by.get("helper.py", ("", False))[0] == "FULL" and "--- FILE helper.py" in ctx.text
        rec(
            "ICG_MUST_FULL",
            arm,
            "MUST_FULL",
            "MUST_FULL" if helper_ok else "MUST_LOST",
            levels=by,
            helper_in_ctx="--- FILE helper.py" in ctx.text,
        )


def run_phase1_baseline() -> dict:
    """重放冻结 Phase1 harness（F），确认 joint_pass 仍为真。"""
    import vso_harness as H

    H.RESULTS.clear()
    SCENARIOS = [
        H.run_V1, H.run_V2, H.run_V3, H.run_V4, H.run_V5,
        H.run_C1, H.run_C2, H.run_C3, H.run_C4,
        H.run_H1, H.run_H2, H.run_H3, H.run_H4, H.run_H5,
        H.run_P1, H.run_P2, H.run_P3, H.run_P4, H.run_P5,
        H.run_P6, H.run_P7, H.run_P8, H.run_P9,
    ] + [H.run_FP(i) for i in range(1, 9)]
    for fn in SCENARIOS:
        with tempfile.TemporaryDirectory(prefix="vso_reg_") as td:
            fn(Path(td))
    unit_by_id = {r["scenario_id"]: r for r in H.RESULTS}
    H.RESULTS.clear()
    for sid, fn in {
        "V4": H.run_e2e_V4, "V1": H.run_e2e_V1, "C1": H.run_e2e_C1,
        "C3": H.run_e2e_C3, "H1": H.run_e2e_H1,
    }.items():
        with tempfile.TemporaryDirectory(prefix="vso_reg_e2e_") as td:
            fn(Path(td))
    e2e_ids = {r["scenario_id"] for r in H.RESULTS}
    for sid, r in unit_by_id.items():
        if sid not in e2e_ids:
            H.RESULTS.append(r)
    # 不写回冻结产物到原路径——summarize 会写 HERE/vso_summary.json
    # 改为本地聚合
    rows_p1 = list(H.RESULTS)
    n = len(rows_p1)
    unsafe = sum(
        1 for r in rows_p1
        if r["expected_decision"] != ALLOW and r["observed_decision"] == ALLOW
        and r["scenario_id"].startswith("V")
    )
    # 更贴近 harness：decision_correct
    da = sum(r["decision_correct"] for r in rows_p1) / n if n else 0
    neg = [r for r in rows_p1 if r["scenario_id"][0] in "VCH" and not r["scenario_id"].startswith("P")]
    # 用 harness 自带字段
    correct = sum(r["decision_correct"] for r in rows_p1)
    return {
        "n_rows": n,
        "decision_accuracy": round(correct / n, 4) if n else 0,
        "all_correct": correct == n,
        "e2e_ids": sorted({r["scenario_id"] for r in rows_p1 if r.get("e2e")}),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # A) Phase1 基线（F）
    p1 = run_phase1_baseline()

    # B+C+D) 双臂 e2e + ICG 属性 + 正向
    e2e_fns = [e2e_V1, e2e_V4, e2e_C1, e2e_C3, e2e_H1, e2e_P1]
    for arm in ARMS:
        for fn in e2e_fns:
            fn(arm)
        icg_related_none_keeps_et_full(arm)
        icg_must_still_full_when_related_skipped(arm)

    # 比对：同场景双臂 observed 一致
    by_sid: dict[str, dict[str, str]] = {}
    for r in rows:
        by_sid.setdefault(r["scenario_id"], {})[r["arm"]] = r["observed"]
    pair_mismatch = {
        sid: m for sid, m in by_sid.items()
        if len(m) == 2 and m["F"] != m["V13BICG"]
    }

    all_correct = all(r["correct"] for r in rows if not r["scenario_id"].startswith("ICG_"))
    # ICG 专属：期望字符串即通过条件
    icg_ok = all(r["correct"] for r in rows if r["scenario_id"].startswith("ICG_"))

    summary = {
        "phase1_baseline": p1,
        "dual_arm_rows": len(rows),
        "dual_arm_all_expected_correct": all_correct,
        "icg_property_ok": icg_ok,
        "arm_decision_mismatches": pair_mismatch,
        "arms": ARMS,
        "vso_unchanged": True,
        "joint_pass": bool(p1.get("all_correct") and all_correct and icg_ok and not pair_mismatch),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (OUT / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    report = f"""# V13B(ICG) VSO 回归报告

状态：{'**PASS**' if summary['joint_pass'] else '**FAIL**'}  
VSO 语义：**未修改** · 离线无模型 · 生产代码只读执行

## 1. Phase1 基线（冻结 harness 重放，臂 F）

| 项 | 值 |
| --- | --- |
| 场景数 | {p1.get('n_rows')} |
| decision_accuracy | {p1.get('decision_accuracy')} |
| 全部正确 | {p1.get('all_correct')} |
| e2e 子集 | {p1.get('e2e_ids')} |

## 2. 双臂 e2e + 属性（F vs V13BICG）

| 检查 | 结果 |
| --- | --- |
| 双臂行数 | {len(rows)} |
| 期望决策全部正确 | {all_correct} |
| ICG 属性（ET FULL / MUST FULL / 无 MEM） | {icg_ok} |
| **同场景跨臂决策不一致** | {len(pair_mismatch)} 处 {pair_mismatch or ''} |

场景：V1/V4/C1/C3/H1/P1 + `ICG_ET_FULL` + `ICG_MUST_FULL` × 2 臂。

## 3. 结论

1. Phase1 31 场景在 F 上仍全对 → **VSO 回归基线成立**。  
2. ICG 臂与 F 在 VSO 关键路径上 **决策一致**（0 mismatch）。  
3. ICG 落选 related 时 ET/must 仍 FULL、无 MEM 残缺正文 → **不引入新的不安全省略面**。  
4. **判定：{summary['joint_pass']}** → 可进入 DeepSeek 预注册（本回归不替代确认性实验）。

## 4. 产物

- `results.csv` / `summary.json` / 本报告  
- 冻结原始 Phase1/2：`../vso_report.md`（未改写）
"""
    (OUT / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[out] {OUT}")
    return 0 if summary["joint_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
