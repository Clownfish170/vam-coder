#!/usr/bin/env python
"""P2 实验3：Critical Information Retention Evaluation（预注册 v1 §8）。

数据：P1 的 vam_coder_v1.2_F + P2 全部 7 臂（episode_logs 跨两目录）。
- CMR_context（预注册主口径）：必要信息点的值出现在该步 user.context（context.txt）
  全文的比例。
- CMR_visible（补充解释口径，明确标注 secondary）：值出现在 context ∪ 指令 ∪ 历史
  （assistant 消息）= 该步模型可见面。
- IRR（文件单元，micro 聚合）：|注入文件 − 该步必要文件| / |注入文件|；注入=EXPAND+DIGEST。
- MEPR：按预注册归 P3 受控污染，本轮=NA。
- 匹配规则（工程细节，manifest 披露）：值为精确子串；len(value)<4 用词边界正则防误配。
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1DIR = HERE.parent / "p1_validation"
TASKS_JSON = Path(__file__).resolve().parents[2] / "tasks_p1_validation" / "p1_tasks.json"
PREREG_SHA256 = "088898a3aec9d08411864ea03ff79ac7ff3e78411ed34a58de89ecd0881cc7ed"

# 预注册 §8 指定的 CIRE 组合：主实验 F + 消融1(E) + 消融2(H) + 消融4(no_oprime)
PREREG_ARMS = {
    "vam_coder_v1.2_F", "vam_coder_v1.2_E", "vam_coder_v1.2_H",
    "vam_coder_v1.2_F_ablate_no_oprime",
}
ALL_ARMS_ORDER = [
    "vam_coder_v1.2_F",
    "vam_coder_v1.2_E",
    "vam_coder_v1.2_H",
    "vam_coder_v1.2_F_ablate_no_must_closure",
    "vam_coder_v1.2_F_ablate_no_oprime",
    "vam_coder_v1.2_F_ablate_history_redact",
    "vam_coder_v1.3_V13B",
    "vam_coder_v1.2_E_ablate_no_must_closure",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_matcher(value: str):
    if len(value) < 4:
        pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])")
        return lambda text: bool(pat.search(text))
    v = value
    return lambda text: v in text


def extract_files(text: str) -> set[str]:
    return set(re.findall(r"\b[\w]+\.py\b", text))


def arch_of(ep_id: str) -> str | None:
    # 最长优先：避免 vam_coder_v1.2_F_ablate_* 被前缀误判为 vam_coder_v1.2_F
    for a in sorted(ALL_ARMS_ORDER, key=len, reverse=True):
        if f"_{a}_" in ep_id:
            return a
    return None


def load_episodes():
    """跨 P1/P2 收集 episode → (task, arch, rep, family, difficulty, steps 信息)。"""
    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    meta = {e["id"]: e for e in tasks_doc["episodes"]}
    info_by_task = {e["id"]: e["required_info_points"] for e in tasks_doc["episodes"]}
    eps = {}
    for root in (P1DIR / "episode_logs", HERE / "episode_logs"):
        if not root.exists():
            continue
        for ep_dir in root.iterdir():
            if not ep_dir.is_dir():
                continue
            ep_id = ep_dir.name
            arch = arch_of(ep_id)
            if arch is None:
                continue
            core, rep_s = ep_id.rsplit("_R", 1)
            task = next(t for t in meta if core.startswith(t + "_"))
            # 步数与 step 名单
            steps_dir = ep_dir / "runner_out" / "episodes" / task / f"vam_coder_{'' if False else ''}"
            # baseline dir 解析：直接 glob
            step_dirs = sorted((ep_dir / "runner_out" / "episodes" / task).glob("*/steps/*"))
            if not step_dirs:
                continue
            eps[ep_id] = {
                "episode_id": ep_id, "task_id": task, "architecture": arch,
                "rep": int(rep_s), "family": meta[task]["family"],
                "difficulty": meta[task]["difficulty"],
                "steps": {},  # step -> {context, user_msg, history_text}
            }
            # 读每步 context/messages
            by_step = defaultdict(dict)
            for sd in step_dirs:
                step = sd.name
                ctx_p = sd / "context.txt"
                msg_p = sd / "messages.json"
                ctx = ctx_p.read_text(encoding="utf-8") if ctx_p.exists() else ""
                msgs = json.loads(msg_p.read_text(encoding="utf-8")) if msg_p.exists() else []
                user = msgs[-1]["content"] if msgs else ""
                # 历史 = 除最后一条 user 外的所有消息（system+assistant）
                hist = "\n".join(m["content"] for m in msgs[:-1])
                by_step[step] = {"context": ctx, "user": user, "history": hist}
            eps[ep_id]["steps"] = dict(by_step)
    return eps, info_by_task, meta


def main() -> int:
    eps, info_by_task, meta = load_episodes()
    print(f"episodes loaded: {len(eps)}")

    step_rows = []
    # 必要文件集合：locator 中出现的 *.py（指令型 locator 无文件 → 空集）
    for ep_id, e in sorted(eps.items()):
        task = e["task_id"]
        points = info_by_task.get(task, [])
        steps = e["steps"]
        for step, texts in steps.items():
            step_idx = int(step.replace("step", ""))
            ctx, user_msg, hist = texts["context"], texts["user"], texts["history"]
            # 注入文件（审计）：EXPAND+DIGEST（读 injection_audit）
            # baseline 目录名
            bdirs = [d.name for d in (P1DIR / "episode_logs" / ep_id / "runner_out" / "episodes" / task).glob("*")] \
                if (P1DIR / "episode_logs" / ep_id).exists() else \
                [d.name for d in (HERE / "episode_logs" / ep_id / "runner_out" / "episodes" / task).glob("*")]
            injected, needed_files_step = set(), set()
            aud_p = (P1DIR if (P1DIR / "episode_logs" / ep_id).exists() else HERE) / \
                "episode_logs" / ep_id / "runner_out" / "episodes" / task / \
                (bdirs[0] if bdirs else "") / "logs" / "injection_audit.jsonl"
            if aud_p.exists():
                for line in aud_p.read_text(encoding="utf-8").splitlines():
                    a = json.loads(line)
                    if a.get("step") != step:
                        continue
                    for c in a.get("checks", []):
                        if c["action"] in ("EXPAND", "DIGEST"):
                            injected.add(c["file"])
                    break
            for p in points:
                if step_idx not in p["needed_by_steps"]:
                    continue
                matcher = make_matcher(p["value"])
                in_ctx = matcher(ctx)
                in_user = matcher(user_msg)
                in_hist = matcher(hist)
                loc_files = extract_files(p["locator"])
                needed_files_step |= loc_files
                step_rows.append({
                    "episode_id": ep_id, "task_id": task,
                    "architecture": e["architecture"], "rep": e["rep"],
                    "family": e["family"], "difficulty": e["difficulty"],
                    "step": step, "point_id": p["id"], "point_type": p["type"],
                    "redundant_in_instruction": int(p["redundant_in_instruction"]),
                    "value": p["value"], "locator": p["locator"],
                    "in_context": int(in_ctx),
                    "in_user_message": int(in_user),
                    "in_history": int(in_hist),
                    "delivered_context": int(in_ctx),
                    "delivered_visible": int(in_user or in_hist or in_ctx),
                })
            # IRR 行（步级）
            if injected:
                miss = len(needed_files_step - injected)
                irr = len(injected - needed_files_step) / len(injected)
                step_rows.append({
                    "episode_id": ep_id, "task_id": task,
                    "architecture": e["architecture"], "rep": e["rep"],
                    "family": e["family"], "difficulty": e["difficulty"],
                    "step": step, "point_id": "__IRR_STEP__", "point_type": "irr",
                    "redundant_in_instruction": "", "value": "", "locator": "",
                    "in_context": "", "in_user_message": "", "in_history": "",
                    "delivered_context": "", "delivered_visible": "",
                    "n_injected_files": len(injected),
                    "n_needed_files": len(needed_files_step),
                    "n_needed_missing": miss,
                    "n_irrelevant_injected": len(injected - needed_files_step),
                    "irr_step": f"{irr:.4f}",
                })

    # 写步级明细
    fields = ["episode_id", "task_id", "architecture", "rep", "family", "difficulty",
              "step", "point_id", "point_type", "redundant_in_instruction",
              "value", "locator", "in_context", "in_user_message", "in_history",
              "delivered_context", "delivered_visible",
              "n_injected_files", "n_needed_files", "n_needed_missing",
              "n_irrelevant_injected", "irr_step"]
    with (HERE / "cire_step_delivery.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in step_rows:
            w.writerow(r)

    # ---------------- 汇总
    pt_rows = [r for r in step_rows if r["point_id"] != "__IRR_STEP__"]
    irr_rows = [r for r in step_rows if r["point_id"] == "__IRR_STEP__"]
    summary = []
    for arch in ALL_ARMS_ORDER:
        sel = [r for r in pt_rows if r["architecture"] == arch]
        if not sel:
            continue
        n = len(sel)
        cmr_ctx = sum(int(r["delivered_context"]) for r in sel) / n
        cmr_vis = sum(int(r["delivered_visible"]) for r in sel) / n
        by_type = {}
        for t in ("implementation", "interface", "critical_data", "history"):
            sub = [r for r in sel if r["point_type"] == t]
            if sub:
                by_type[t] = (
                    sum(int(r["delivered_context"]) for r in sub) / len(sub),
                    sum(int(r["delivered_visible"]) for r in sub) / len(sub),
                    len(sub),
                )
        red = [r for r in sel if int(r["redundant_in_instruction"]) == 1]
        hid = [r for r in sel if int(r["redundant_in_instruction"]) == 0]
        # IRR micro
        isel = [r for r in irr_rows if r["architecture"] == arch]
        tot_inj = sum(int(r["n_injected_files"]) for r in isel)
        tot_irr = sum(int(r["n_irrelevant_injected"]) for r in isel)
        tot_miss = sum(int(r["n_needed_missing"]) for r in isel)
        irr_micro = (tot_irr / tot_inj) if tot_inj else float("nan")
        summary.append({
            "architecture": arch,
            "in_prereg_cire_set": int(arch in PREREG_ARMS),
            "point_steps": n,
            "CMR_context": f"{cmr_ctx:.4f}",
            "CMR_visible_secondary": f"{cmr_vis:.4f}",
            "CMR_context_impl": f"{by_type.get('implementation', (float('nan'),)*3)[0]:.4f}",
            "CMR_context_interface": f"{by_type.get('interface', (float('nan'),)*3)[0]:.4f}",
            "CMR_context_critical_data": f"{by_type.get('critical_data', (float('nan'),)*3)[0]:.4f}",
            "CMR_context_history": f"{by_type.get('history', (float('nan'),)*3)[0]:.4f}",
            "CMR_context_redundant": f"{(sum(int(r['delivered_context']) for r in red)/len(red)):.4f}" if red else "NA",
            "CMR_context_hidden": f"{(sum(int(r['delivered_context']) for r in hid)/len(hid)):.4f}" if hid else "NA",
            "IRR_micro_file_units": f"{irr_micro:.4f}",
            "n_injected_file_units": tot_inj,
            "n_irrelevant_injected_units": tot_irr,
            "n_needed_file_missing": tot_miss,
            "MEPR": "NA（预注册：归 P3 受控污染实验）",
        })
    fields2 = list(summary[0].keys())
    with (HERE / "cire_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields2)
        w.writeheader()
        w.writerows(summary)

    manifest = {
        "schema": "p2-cire-manifest-v1",
        "generated_at": now(),
        "prereg_sha256": PREREG_SHA256,
        "prereg_set": sorted(PREREG_ARMS),
        "arms_computed": sorted({r["architecture"] for r in pt_rows}),
        "operationalization": {
            "primary_CMR": "delivered = value 匹配于该步 user.context 全文（context.txt），预注册 §8 字面口径",
            "secondary_CMR_visible": "context ∪ 该步指令 ∪ 历史 assistant 消息（解释性补充，不替代主口径）",
            "match_rule": "精确子串；len(value)<4 用词边界正则",
            "IRR_unit": "文件（注入=EXPAND+DIGEST；必要文件=信息点 locator 中的 *.py）",
            "IRR_aggregation": "micro（合并分子分母）",
            "MEPR": "NA — 预注册归 P3 受控污染",
        },
        "counts": {
            "episodes": len(eps),
            "point_step_rows": len(pt_rows),
            "irr_step_rows": len(irr_rows),
        },
    }
    (HERE / "cire_analysis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print()
    for s in summary:
        print(f"{s['architecture']}: CMR_ctx={s['CMR_context']} CMR_vis={s['CMR_visible_secondary']} "
              f"IRR={s['IRR_micro_file_units']} missing_files={s['n_needed_file_missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
