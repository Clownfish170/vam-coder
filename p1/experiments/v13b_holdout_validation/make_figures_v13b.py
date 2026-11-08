#!/usr/bin/env python
"""V1.3-B Round 2 图表：轴与图例一律使用完整架构英文标识。"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
ARCHS = [
    "vam_coder_v1.2_E",
    "vam_coder_v1.2_F",
    "vam_coder_v1.3_V13B",
    "memory_off",
    "symbol_full_read",
]
COLORS = {
    "vam_coder_v1.2_E": "#4C72B0",
    "vam_coder_v1.2_F": "#DD8452",
    "vam_coder_v1.3_V13B": "#55A868",
    "memory_off": "#C44E52",
    "symbol_full_read": "#8172B3",
}

raw = list(csv.DictReader((HERE / "raw_results.csv").open(encoding="utf-8")))
metrics = {r["key"]: r for r in csv.DictReader((HERE / "metrics_summary.csv").open(encoding="utf-8"))
           if r["scope"] == "architecture"}
task_metrics = {
    (r["key"].split(":")[0], r["key"].split(":")[1]): r
    for r in csv.DictReader((HERE / "metrics_summary.csv").open(encoding="utf-8"))
    if r["scope"] == "task_architecture"
}
fails = list(csv.DictReader((HERE / "failure_analysis.csv").open(encoding="utf-8")))

ep = defaultdict(lambda: {"prompt": 0, "success": True, "arch": "", "task": ""})
for r in raw:
    e = ep[r["episode_id"]]
    e["prompt"] += int(r["prompt_tokens"])
    e["success"] = e["success"] and r["eval_success"] == "1"
    e["arch"] = r["architecture"]
    e["task"] = r["task_id"]
ep_prompt: dict[str, list[int]] = defaultdict(list)
ep_succ: dict[str, list[int]] = defaultdict(list)
ep_task_succ: dict[tuple, list[int]] = defaultdict(list)
for v in ep.values():
    ep_prompt[v["arch"]].append(v["prompt"])
    ep_succ[v["arch"]].append(int(v["success"]))
    ep_task_succ[(v["task"], v["arch"])].append(int(v["success"]))

FIG.mkdir(exist_ok=True)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160)
    plt.close(fig)
    print("wrote", name)


def fig1():
    esr = [float(metrics[a]["ESR"]) * 100 for a in ARCHS]
    lo = [float(metrics[a]["ESR_ci95_low"]) * 100 for a in ARCHS]
    hi = [float(metrics[a]["ESR_ci95_high"]) * 100 for a in ARCHS]
    err = [[e - l for e, l in zip(esr, lo)], [h - e for e, h in zip(esr, hi)]]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(ARCHS))
    ax.bar(x, esr, color=[COLORS[a] for a in ARCHS], width=0.55, yerr=err,
           capsize=6, error_kw=dict(ecolor="black", lw=1.1))
    for i, a in enumerate(ARCHS):
        m = metrics[a]
        ax.text(i, esr[i] + 3.2, f"{m['success']}/{m['episodes']}", ha="center", fontsize=10)
        ax.text(i, 0.8, f"CI [{lo[i]:.1f}, {hi[i]:.1f}]", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(ARCHS, rotation=18, ha="right", fontsize=9)
    ax.set_ylabel("ESR 任务成功率 (%)（全步通过 episode 比例）")
    ax.set_title("图1  各架构任务成功率（ESR, %）对比 — Wilson 95% CI\n"
                 "每架构 n=12 tasks × R=2 = 24 episodes；Qwen2.5-Coder-1.5B-Instruct Q6_K；round2 holdout")
    ax.set_ylim(0, 30)
    save(fig, "fig1_esr_by_architecture.png")


def fig2():
    means = [float(metrics[a]["prompt_tokens_mean_per_episode"]) for a in ARCHS]
    fig, ax = plt.subplots(figsize=(10.5, 5))
    x = np.arange(len(ARCHS))
    ax.bar(x, means, color=[COLORS[a] for a in ARCHS], width=0.5, zorder=1)
    rng = np.random.default_rng(11)
    for i, a in enumerate(ARCHS):
        vals = ep_prompt[a]
        pts = np.full(len(vals), i) + rng.uniform(-0.15, 0.15, len(vals))
        ax.scatter(pts, vals, s=13, color="black", alpha=0.5, zorder=2)
        ax.text(i, means[i] + 16, f"μ={means[i]:.1f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ARCHS, rotation=18, ha="right", fontsize=9)
    ax.set_ylabel("prompt_tokens / episode（tokens）")
    ax.set_title("图2  各架构平均 prompt_tokens 对比（柱=均值，点=24 episode 实测）\n"
                 "prompt_tokens=完整请求 prompt 长度（主要上下文开销）；头部统一为 [ctx] 消除臂名伪影")
    ax.set_ylim(0, max(max(m for m in means), 850) + 60)
    save(fig, "fig2_prompt_by_architecture.png")


def fig3():
    fig, ax = plt.subplots(figsize=(9.5, 5))
    for a in ARCHS:
        m = metrics[a]
        x = float(m["prompt_tokens_mean_per_episode"])
        y = float(m["ESR"]) * 100
        ylo, yhi = float(m["ESR_ci95_low"]) * 100, float(m["ESR_ci95_high"]) * 100
        # x CI 来自 bootstrap（architecture_point prompt_per_episode）
        boot_rows = list(csv.DictReader((HERE / "bootstrap_results.csv").open(encoding="utf-8")))
        br = [b for b in boot_rows if b["scope"] == "architecture_point"
              and b["key"] == a and b["metric"] == "prompt_per_episode"][0]
        xlo, xhi = float(br["ci95_low"]), float(br["ci95_high"])
        ax.errorbar(x, y, xerr=[[x - xlo], [xhi - x]],
                    yerr=[[y - ylo], [yhi - y]], fmt="o",
                    color=COLORS[a], markersize=9, capsize=4,
                    label=f"{a} (TPAE={float(m['TPAE']):.0f})")
        ax.annotate(a, (x, y), textcoords="offset points", xytext=(7, 5),
                    fontsize=8, color=COLORS[a])
    ax.set_xlabel("平均 prompt_tokens / episode（tokens，task-cluster bootstrap 95% CI）")
    ax.set_ylabel("ESR 成功率（%，Wilson 95% CI）")
    ax.set_title("图3  成功率与 Token 开销权衡（每点=一个架构；n=24 episodes/架构）\n"
                 "左下更优：更低上下文开销 + 更高成功率")
    ax.set_ylim(-3, 30)
    ax.legend(fontsize=7.5, loc="upper right")
    ax.grid(alpha=0.3)
    save(fig, "fig3_tradeoff_by_architecture.png")


def fig4():
    tasks = sorted({k[0] for k in task_metrics})
    fig, ax = plt.subplots(figsize=(11.5, 5))
    w = 0.38
    x = np.arange(len(tasks))
    d_f = [
        float(task_metrics[(t, "vam_coder_v1.3_V13B")]["prompt_tokens_mean_per_episode"])
        - float(task_metrics[(t, "vam_coder_v1.2_F")]["prompt_tokens_mean_per_episode"])
        for t in tasks
    ]
    d_e = [
        float(task_metrics[(t, "vam_coder_v1.3_V13B")]["prompt_tokens_mean_per_episode"])
        - float(task_metrics[(t, "vam_coder_v1.2_E")]["prompt_tokens_mean_per_episode"])
        for t in tasks
    ]
    b1 = ax.bar(x - w / 2, d_f, width=w, color=COLORS["vam_coder_v1.3_V13B"],
                label="Δprompt vam_coder_v1.3_V13B − vam_coder_v1.2_F")
    b2 = ax.bar(x + w / 2, d_e, width=w, color=COLORS["vam_coder_v1.2_E"],
                label="Δprompt vam_coder_v1.3_V13B − vam_coder_v1.2_E")
    for bars in (b1, b2):
        for rect in bars:
            h = rect.get_height()
            if abs(h) >= 0.5:
                ax.text(rect.get_x() + rect.get_width() / 2,
                        h + (1.2 if h >= 0 else -3.6), f"{h:+.0f}",
                        ha="center", fontsize=7)
    # 任务级 Δ成功（V13B vs F / vs E）
    for j, t in enumerate(tasks):
        s_b = sum(ep_task_succ[(t, "vam_coder_v1.3_V13B")])
        s_f = sum(ep_task_succ[(t, "vam_coder_v1.2_F")])
        s_e = sum(ep_task_succ[(t, "vam_coder_v1.2_E")])
        ax.text(j, -16, f"Δsucc {s_b - s_f:+d}/{s_b - s_e:+d}", ha="center",
                fontsize=6.5, color="#333333")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("v13_", "") for t in tasks], rotation=30, ha="right")
    ax.set_ylabel("Δ 平均 prompt_tokens / episode（tokens）")
    ax.set_title("图4  任务级配对差值：vam_coder_v1.3_V13B 相对 vam_coder_v1.2_F 与 vam_coder_v1.2_E（逐任务，非总体均值）\n"
                 "轴下 Δsucc = 任务级成功数差（V13B−F / V13B−E，每任务 2 episodes）")
    ax.legend(fontsize=8)
    ax.set_ylim(-30, max(max(d_e + d_f) + 20, 25))
    save(fig, "fig4_task_deltas_v13b.png")


def fig5():
    mech_order = ["model_noop", "model_wrong_implementation", "model_no_edit",
                  "protocol_violation", "infrastructure_error"]
    labels = {
        "model_noop": "model_noop（输出未改动）",
        "model_wrong_implementation": "model_wrong_implementation（改动但错误）",
        "model_no_edit": "model_no_edit（返回 NO_EDIT）",
        "protocol_violation": "protocol_violation",
        "infrastructure_error": "infrastructure_error",
    }
    counts = {a: Counter() for a in ARCHS}
    for fr in fails:
        for mech in fr["mechanisms"].split(";"):
            if mech:
                counts[fr["architecture"]][mech] += 1
    fig, ax = plt.subplots(figsize=(11, 4.8))
    x = np.arange(len(ARCHS))
    bottom = np.zeros(len(ARCHS))
    palette = ["#8172B3", "#C44E52", "#937860", "#555555", "#DA8BC3"]
    for k, mech in enumerate(mech_order):
        vals = np.array([counts[a][mech] for a in ARCHS], dtype=float)
        if vals.sum() == 0:
            continue
        ax.bar(x, vals, bottom=bottom, color=palette[k % len(palette)], label=labels[mech])
        bottom += vals
    for i, a in enumerate(ARCHS):
        ax.text(i, bottom[i] + 0.7, f"{int(bottom[i])}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ARCHS, rotation=18, ha="right", fontsize=9)
    ax.set_ylabel("失败机制计数（步级）")
    ax.set_title("图5  各架构失败原因分布（步级机制；每架构 48 步）\n"
                 "rev3 §4.5 错误分类：protocol / architecture / infrastructure 均为 0")
    ax.legend(fontsize=8, loc="upper left")
    save(fig, "fig5_failures_by_architecture.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    print("ALL DONE")
