#!/usr/bin/env python
"""P0 功率分析：用 round3 的 task 级真实数据为 P1（扩任务轮）估计样本量依据。

方法（预注册口径）：
- 任务为配对/聚类单位；task-level 差值 d_t = (该任务臂A成功均值 − 臂B成功均值)。
- 检验：task 级 sign-flip 置换（双侧 α=0.05，2000 次翻转）。
- 成功率数据生成：按 round3 各 task×arch 观测成功率为 p，伯努利抽 R 次（探索性近似）。
- Token：按 round3 各 task×arch 观测 episode prompt_tokens 重抽（R 次有放回）。
- 输出：observed-effect 功率表 + N=50,R=5 的 ΔESR 最小可检测效应（MDE，80% 功率）。
输出 power_analysis.csv（写入本目录）。
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROUND3 = HERE.parent / "round3_deepseek_flash" / "raw_results.csv"
B_SIM = 2000
B_FLIP = 2000
ALPHA = 0.05
RNG = np.random.default_rng(20261102)  # 与主分析同源的 bootstrap seed

ARCHS = [
    "vam_coder_v1.2_E",
    "vam_coder_v1.2_F",
    "vam_coder_v1.3_V13B",
    "memory_off",
    "symbol_full_read",
]
PAIRS = [
    ("vam_coder_v1.2_F", "vam_coder_v1.2_E"),
    ("vam_coder_v1.2_F", "memory_off"),
    ("vam_coder_v1.2_F", "symbol_full_read"),
    ("vam_coder_v1.3_V13B", "vam_coder_v1.2_F"),
]


def load_task_stats():
    """→ succ[task][arch]∈{0..R_obs}, prompt[task][arch]=[ep_tokens...]"""
    succ: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    prompt: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    reps: dict[str, set] = defaultdict(set)
    rows = list(csv.DictReader(ROUND3.open(encoding="utf-8")))
    ep: dict[str, dict] = {}
    for r in rows:
        key = r["episode_id"]
        e = ep.setdefault(key, {"task": r["task_id"], "arch": r["architecture"],
                                "succ": True, "p": 0})
        e["succ"] = e["succ"] and r["eval_success"] == "1"
        e["p"] += int(r["prompt_tokens"])
    for e in ep.values():
        t, a = e["task"], e["arch"]
        succ[t][a] += int(e["succ"])
        prompt[t][a].append(e["p"])
        reps[t].add(1)
    return succ, prompt


def signflip_p(diffs: np.ndarray, signs: np.ndarray) -> float:
    """向量化 sign-flip：signs 形状 (B_FLIP, N)。"""
    obs = abs(diffs.mean())
    null = np.abs((signs * diffs[None, :]).mean(axis=1))
    return float((np.sum(null >= obs) + 1) / (B_FLIP + 1))


def power_esr(succ, tasks, arch_a, arch_b, N, R, rng) -> float:
    signs = rng.choice([-1.0, 1.0], size=(B_FLIP, N))
    hits = 0
    r_obs = 2  # round3 每任务 2 reps
    for _ in range(B_SIM):
        sample = rng.choice(tasks, size=N, replace=True)
        diffs = np.empty(N)
        for i, t in enumerate(sample):
            pa = succ[t][arch_a] / r_obs
            pb = succ[t][arch_b] / r_obs
            diffs[i] = rng.binomial(R, pa) / R - rng.binomial(R, pb) / R
        if signflip_p(diffs, signs) < ALPHA:
            hits += 1
    return hits / B_SIM


def power_token(prompt, tasks, arch_a, arch_b, N, R, rng) -> float:
    signs = rng.choice([-1.0, 1.0], size=(B_FLIP, N))
    hits = 0
    for _ in range(B_SIM):
        sample = rng.choice(tasks, size=N, replace=True)
        diffs = np.empty(N)
        for i, t in enumerate(sample):
            va = rng.choice(prompt[t][arch_a], size=R, replace=True).mean()
            vb = rng.choice(prompt[t][arch_b], size=R, replace=True).mean()
            diffs[i] = va - vb
        if signflip_p(diffs, signs) < ALPHA:
            hits += 1
    return hits / B_SIM


def mde_esr(succ, tasks, arch_base, arch_comp, N, R, rng, grid=None) -> float | None:
    """对称构造：两臂均以 arch_base 的观测概率为底，comp 臂整体下移 δ。
    找 power≥0.8 的最小 δ（即该设计的最小可检测 ΔESR）。"""
    grid = grid or [i / 100 for i in range(2, 31, 2)]
    signs = rng.choice([-1.0, 1.0], size=(B_FLIP, N))
    r_obs = 2
    for delta in grid:
        hits = 0
        for _ in range(B_SIM):
            sample = rng.choice(tasks, size=N, replace=True)
            diffs = np.empty(N)
            for i, t in enumerate(sample):
                pa = succ[t][arch_base] / r_obs
                pb = max(0.0, pa - delta)
                diffs[i] = rng.binomial(R, pa) / R - rng.binomial(R, pb) / R
            if signflip_p(diffs, signs) < ALPHA:
                hits += 1
        if hits / B_SIM >= 0.80:
            return delta
    return None


def main() -> int:
    succ, prompt = load_task_stats()
    tasks = sorted(succ)
    assert len(tasks) == 12

    # round3 观测差值
    def obs_delta(a, b, metric="esr"):
        if metric == "esr":
            va = np.mean([succ[t][a] / 2 for t in tasks])
            vb = np.mean([succ[t][b] / 2 for t in tasks])
        else:
            va = np.mean([np.mean(prompt[t][a]) for t in tasks])
            vb = np.mean([np.mean(prompt[t][b]) for t in tasks])
        return float(va - vb)

    out = []
    designs = [(12, 2), (24, 3), (40, 5), (50, 5)]
    for a, b in PAIRS:
        d_esr = obs_delta(a, b, "esr")
        d_tok = obs_delta(a, b, "prompt")
        for N, R in designs:
            p_esr = power_esr(succ, tasks, a, b, N, R, RNG)
            p_tok = power_token(prompt, tasks, a, b, N, R, RNG)
            out.append({
                "kind": "observed_effect", "pair": f"{a} − {b}",
                "N_tasks": N, "R": R,
                "observed_delta_ESR": f"{d_esr:.4f}",
                "observed_delta_prompt_tokens": f"{d_tok:.1f}",
                "power_ESR": f"{p_esr:.3f}",
                "power_prompt_tokens": f"{p_tok:.3f}",
                "method": f"task-cluster sign-flip, α={ALPHA}, B_sim={B_SIM}, flips={B_FLIP}",
                "seed": 20261102,
            })

    # MDE：F vs E、F vs memory_off 在 N=50,R=5 下的 ΔESR 最小可检测效应（80% 功率）
    mde_rows = []
    for a, b in [("vam_coder_v1.2_F", "vam_coder_v1.2_E"),
                 ("vam_coder_v1.2_F", "memory_off")]:
        mde = mde_esr(succ, tasks, a, b, 50, 5, RNG)
        mde_rows.append({
            "kind": "MDE_ESR", "pair": f"{a} − {b}",
            "N_tasks": 50, "R": 5,
            "observed_delta_ESR": f"{obs_delta(a, b):.4f}",
            "observed_delta_prompt_tokens": "",
            "power_ESR": ">=0.80 by construction" if mde else ">0.30 (not reached)",
            "power_prompt_tokens": "",
            "MDE_delta_ESR": f"{mde:.2f}" if mde else "NA",
            "method": "inject δ on comp-arm task rates; min δ with power≥0.80",
            "seed": 20261102,
        })

    fields = ["kind", "pair", "N_tasks", "R", "observed_delta_ESR",
              "observed_delta_prompt_tokens", "power_ESR", "power_prompt_tokens",
              "MDE_delta_ESR", "method", "seed"]
    rows = out + mde_rows
    with (HERE / "power_analysis.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # 控制台摘要
    print("=== observed-effect power (round3-based) ===")
    for r in out:
        print(f"{r['pair']:55s} N={r['N_tasks']:>2} R={r['R']}  "
              f"dESR={r['observed_delta_ESR']:>7} pESR={r['power_ESR']:>5}  "
              f"dTok={r['observed_delta_prompt_tokens']:>7} pTok={r['power_prompt_tokens']:>5}")
    print("=== MDE (N=50, R=5, power≥0.80) ===")
    for r in mde_rows:
        print(f"{r['pair']:55s} MDE_dESR={r['MDE_delta_ESR']}  "
              f"(observed={r['observed_delta_ESR']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
