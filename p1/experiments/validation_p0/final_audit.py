#!/usr/bin/env python
"""Part1 最终审计：只读核对既有研究的哈希/样本数/参数/统计口径/报告数字一致性。
输出 final_audit.json（供总报告引用）。不修改任何实验数据。"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

P1 = Path(__file__).resolve().parents[2]      # p1/
VAM = P1.parent                                # vam-coder/
EXP = {
    "round1_holdout": P1 / "experiments" / "v13_holdout_validation",
    "round2_v13b": P1 / "experiments" / "v13b_holdout_validation",
    "round3_deepseek": P1 / "experiments" / "round3_deepseek_flash",
    "p1_confirmatory": P1 / "experiments" / "p1_validation",
    "p2_ablation": P1 / "experiments" / "p2_ablation",
    "p3_crossmodel": P1 / "experiments" / "p3_crossmodel_qwen",
    "vso": P1 / "experiments" / "vso_fault_injection",
    "validation_p0": P1 / "experiments" / "validation_p0",
}

FROZEN = {
    "rev3_plan": ("p1/experiments/v12_p1_execution/v13_design/v13_m2_validation_plan_rev3.md",
                  "8ceed45d6554ba952a641fbbebb49b4f3eb0f69858c16ba9d58d7025eb9ee13f"),
    "prereg_v1": ("p1/docs/v12f_validation_preregistration.md",
                  "088898a3aec9d08411864ea03ff79ac7ff3e78411ed34a58de89ecd0881cc7ed"),
    "p3a_addendum": ("p1/docs/v12f_validation_preregistration_addendum_p3a.md",
                     "2ce8defff22395fcfe7d48325a7c9f9fc5cd8c867b7f8be7643833dd2e38fffe"),
    "vso_design": ("p1/docs/vso_fault_injection_evaluation_design.md",
                   "0d9c292b2ef7e09fc0d6ddef137d163ca91a342c1e8144341fce3d3725f1746b"),
    "holdout_tasks": ("p1/tasks_v13_holdout/holdout_tasks.json",
                      "59cebdd9471ae07d1a416f8b9f7249002087454523df062d8b4e6db68849f4d4"),
    "holdout_manifest": ("p1/tasks_v13_holdout/holdout_manifest.json",
                         "fcb8762f1ada7bfb57a533db3d0f20d2d0282892bbf4f05ba7b7163418bb9c05"),
    "p1_tasks": ("p1/tasks_p1_validation/p1_tasks.json",
                 "d44445b2b8bff0a4338e9694194384235f73d0ea20b3d9550ae5d297c6f8f33b"),
    "p1_tasks_manifest": ("p1/tasks_p1_validation/p1_tasks_manifest.json",
                          "ee78e8258970124077ea4b16bf386c7e5ae42b85d26734ddca3d17471bd635d2"),
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def count_eps_and_steps(root: Path) -> tuple[int, int]:
    eps = 0
    steps = 0
    if not root.exists():
        return 0, 0
    for ep in root.iterdir():
        if not ep.is_dir():
            continue
        ps = ep / "runner_out" / "per_step.csv"
        if ps.exists():
            eps += 1
            with ps.open(newline="", encoding="utf-8") as f:
                steps += sum(1 for _ in csv.DictReader(f))
    return eps, steps


def main() -> int:
    audit: dict = {"frozen_hashes": {}, "experiments": {}, "run_metas": {},
                   "stat_conventions": {}, "report_spot_checks": {},
                   "git_state": {}, "retest": {}, "discrepancies": []}

    # A. 冻结哈希
    for name, (rel, want) in FROZEN.items():
        p = VAM / rel
        got = sha(p) if p.exists() else "MISSING"
        ok = got == want
        audit["frozen_hashes"][name] = {"expected": want, "actual": got, "match": ok}
        if not ok:
            audit["discrepancies"].append(f"FROZEN MISMATCH: {name}")

    # B. 样本数
    expected = {
        "round1_holdout": (72, 144),
        "round2_v13b": (120, 240),
        "round3_deepseek": (120, 240),
        "p1_confirmatory": (720, 4080),
        "p2_ablation": (1680, 9520),
        "p3_crossmodel": (720, 4080),
    }
    for k, root in EXP.items():
        if k in ("vso", "validation_p0"):
            continue
        eps, steps = count_eps_and_steps(root / "episode_logs")
        audit["experiments"][k] = {
            "episodes": eps, "step_rows": steps,
            "expected_episodes": expected.get(k, (None, None))[0],
            "episodes_match": eps == expected.get(k, (None, None))[0],
        }

    # C. run_meta 参数
    for k in ("p1_confirmatory", "p2_ablation", "p3_crossmodel"):
        rm = EXP[k] / "run_meta.json"
        if not rm.exists():
            audit["discrepancies"].append(f"missing run_meta: {k}")
            continue
        m = json.loads(rm.read_text(encoding="utf-8"))
        audit["run_metas"][k] = {
            "model": m.get("model"), "max_tokens": m.get("max_tokens"),
            "temperature": m.get("temperature"), "seed": m.get("seed"),
            "history_policy": m.get("history_policy"),
            "repetitions": m.get("repetitions"), "randomization_seed": m.get("randomization_seed"),
            "bootstrap_seed": m.get("bootstrap_seed"), "s5": m.get("s5_token_limit"),
            "frozen_hashes_recorded": m.get("frozen_hashes"),
            "architectures": m.get("architectures"),
        }

    # D. 统计口径
    for k in ("p1_confirmatory", "p2_ablation", "p3_crossmodel"):
        am = EXP[k] / "analysis_manifest.json"
        if am.exists():
            a = json.loads(am.read_text(encoding="utf-8"))
            audit["stat_conventions"][k] = {
                "bootstrap_seed": a.get("bootstrap_seed"),
                "bootstrap_B": a.get("bootstrap_B"),
                "cluster": a.get("cluster"),
            }
    audit["stat_conventions"]["prereg_expected"] = {"bootstrap_seed": 20261102,
                                                    "bootstrap_B": 10000, "cluster": "task_id"}

    # E. 报告数字抽查（主表 vs CSV）
    def arm_row(exp, key, scope="architecture"):
        rows = list(csv.DictReader((EXP[exp] / "metrics_summary.csv").open(encoding="utf-8")))
        return next((r for r in rows if r["scope"] == scope and r["key"] == key), None)

    spot = {}
    f = arm_row("p1_confirmatory", "vam_coder_v1.2_F")
    spot["P1_F_ESR_successes"] = f["success"] if f else None
    spot["P1_F_ESR"] = f["ESR"] if f else None
    f2 = arm_row("p1_confirmatory", "memory_off")
    spot["P1_memory_off_ESR"] = f2["ESR"] if f2 else None
    r3 = arm_row("p3_crossmodel", "vam_coder_v1.2_F")
    spot["P3A_F_ESR_successes"] = r3["success"] if r3 else None
    # VSO
    v1s = json.loads((EXP["vso"] / "vso_summary.json").read_text(encoding="utf-8"))
    v2s = json.loads((EXP["vso"] / "phase2_runs" / "vso_phase2_summary.json").read_text(encoding="utf-8"))
    spot["VSO_phase1_joint_pass"] = v1s.get("joint_pass")
    spot["VSO_phase1_rows"] = v1s.get("n_rows")
    spot["VSO_phase2_accuracy"] = v2s.get("decision_accuracy")
    spot["VSO_phase2_scenarios_pass"] = f"{v2s.get('scenarios_pass')}/{v2s.get('scenarios_total')}"
    # 模型不合并检查：P1 vs P3A prompt 绝对值不同（预期）
    spot["tokenizer_note"] = "P1=deepseek / P3A=qwen3.8-flash：绝对 token 禁止横向比较（已在报告约束）"
    audit["report_spot_checks"] = spot

    # F. Git 只读状态
    def git(*args):
        r = subprocess.run(["git", *args], cwd=VAM, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return (r.stdout or "").strip()
    audit["git_state"] = {
        "branch": git("branch", "--show-current"),
        "head": git("log", "--oneline", "-1"),
        "modified_files": git("status", "--short").splitlines()[:40],
        "stash_list": git("stash", "list").splitlines()[:5],
    }

    # G. 协议复测状态
    rs = EXP["validation_p0"] / "protocol_retest_4096" / "retest_summary.json"
    if rs.exists():
        s = json.loads(rs.read_text(encoding="utf-8"))
        audit["retest"] = {"episodes": s.get("episodes"), "resolved_rate": s.get("resolved_rate"),
                           "remaining_trunc_empty": s.get("remaining_trunc_empty"),
                           "max_tokens": s.get("max_tokens")}
    else:
        log = EXP["validation_p0"] / "protocol_retest_4096" / "retest_log.jsonl"
        n = len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0
        audit["retest"] = {"status": "running" if n else "absent", "logged_episodes": n}

    # H. 已知偏差台账（人工整理条目，来自实际执行历史）
    audit["curated_deviations"] = [
        {"id": "D1", "item": "p1_common.py 在 P1/P2 之后新增可选 VAM_API_KEY 鉴权头（P3-A 前）",
         "handling": "P1/P2 run_meta 记录当时的 sha；P3 orchestrator 钉新 sha；SYSTEM_PROMPT/build_messages 哈希全程不变"},
        {"id": "D2", "item": "run_p1_v12.py 在 P2 前新增三个消融开关（history-policy/no-must-closure/no-oprime）",
         "handling": "默认值与冻结配置等价；P2/P3 run_meta 记录 runner sha 19fd9669…"},
        {"id": "D3", "item": "round1–3 为探索轮（含1.5B与早期云轮），不与 P1–P3 确认性数据合并",
         "handling": "prereg §11.3 已冻结该隔离规则"},
        {"id": "D4", "item": "P3-A 一集 RemoteDisconnected（RC_1，零数据）→ 断点补跑完成",
         "handling": "RC_1 行保留在 execution_log；infrastructure 类单列"},
        {"id": "D5", "item": "VSO Phase2 首轮 18 集落在省略不可达任务（判定对、注入未激活）",
         "handling": "归档 execution_log_superseded_vacuous.jsonl，修正映射后重跑；两条断言按冻结字面修正后离线复评（零模型重跑）；fault_safe_calls 字段复评时丢失（N/A，激活改用行为证据）"},
        {"id": "D6", "item": "协议违规 51/51=EMPTY_TRUNC（归因已修 round3 预算标注）→ 4096 受控复测",
         "handling": "隔离目录重跑，不触碰冻结数据"},
        {"id": "D7", "item": "max_tokens 跨阶段：round1/2=1024 → exp6 判定 → round3/P1/P2/P3A=2048",
         "handling": "exp6 判定记录在案；各轮 run_meta 单独记录"},
        {"id": "D8", "item": "P1 任务集为 8 个参数化族（有效独立设计数 < 48）",
         "handling": "prereg §5 披露 + 族级敏感性分析；Part2 新任务集须解决真实独立性"},
        {"id": "D9", "item": "ESR 地板与生成非确定性（1.5B 轮64/72步重复一致；deepseek/qwen仍有抖动）",
         "handling": "任务级聚类 + 非劣界值 + 不作优效主张"},
        {"id": "D10", "item": "Git：分支 p1/v1.1、4 个未提交修改、stash@{0} 存在",
         "handling": "全程零 git 写操作；stash 不动"},
    ]

    audit["unresolved_questions"] = [
        "VSO 文档 §11 的5个歧义按默认值钉死（用户授权冻结时）；FBR=False Block Rate 等口径已入设计冻结记录",
        "双 Token 独立贡献：B/C（符号寻址、静态表示）机制尚未实现——论文中不得主张其收益（任务书约束一致）",
        "KV Cache 显存：无实测，禁止主张（约束4）",
    ]

    out = EXP["validation_p0"] / "final_audit.json"
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 控制台摘要
    bad = [k for k, v in audit["frozen_hashes"].items() if not v["match"]]
    print("frozen hashes:", "ALL MATCH" if not bad else f"MISMATCH: {bad}")
    for k, v in audit["experiments"].items():
        print(f"  {k}: eps={v['episodes']} steps={v['step_rows']} match={v['episodes_match']}")
    print("spot:", json.dumps(audit["report_spot_checks"], ensure_ascii=False))
    print("stat:", json.dumps(audit["stat_conventions"], ensure_ascii=False))
    print("retest:", audit["retest"])
    print("git:", audit["git_state"]["branch"], "|", audit["git_state"]["head"][:60])
    print("discrepancies:", audit["discrepancies"] or "none (frozen layer)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
