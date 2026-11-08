#!/usr/bin/env python
"""P1 图表（预注册配套；轴/图例一律完整架构英文名；数据全部来自本次实验）。"""

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
ARCHS = ["vam_coder_v1.2_F", "memory_off", "symbol_full_read"]
COLORS = {"vam_coder_v1.2_F": "#55A868", "memory_off": "#C44E52",
          "symbol_full_read": "#8172B3"}
DIFFS = ["short", "medium", "long"]

raw = list(csv.DictReader((HERE / "raw_results.csv").open(encoding="utf-8")))
metrics = {r["key"]: r for r in csv.DictReader((HERE / "metrics_summary.csv").open(encoding="utf-8"))
           if r["scope"] == "architecture"}
diff_metrics = {r["key"]: r for r in csv.DictReader((HERE / "metrics_summary.csv").open(encoding="utf-8"))
                if r["scope"] == "difficulty_architecture"}
task_metrics = {r["key"]: r for r in csv.DictReader((HERE / "metrics_summary.csv").open(encoding="utf-8"))
                if r["scope"] == "task_architecture"}
fails = list(csv.DictReader((HERE / "failure_analysis.csv").open(encoding="utf-8")))
families = list(csv.DictReader((HERE / "family_sensitivity.csv").open(encoding="utf-8")))

# episode 级聚合
ep = defaultdict(lambda: {"prompt": 0, "success": True, "arch": "", "task": "",
                          "diff": "", "family": ""})
for r in raw:
    e = ep[r["episode_id"]]
    e["prompt"] += int(r["prompt_tokens"])
    e["success"] = e["success"] and r["eval_success"] == "1"
    e["arch"] = r["architecture"]
    e["task"] = r["task_id"]
    e["diff"] = r["difficulty"]
    e["family"] = r["family"]
ep_prompt = defaultdict(list)
ep_succ = defaultdict(list)
ep_task_prompt = defaultdict(list)
for v in ep.values():
    ep_prompt[v["arch"]].append(v["prompt"])
    ep_succ[v["arch"]].append(int(v["success"]))
    ep_task_prompt[(v["task"], v["arch"])].append(v["prompt"])

FIG.mkdir(exist_ok=True)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160)
    plt.close(fig)
    print("wrote", name)


def fig1():
    """ESR 总体 + 难度分层。"""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    # (a) overall
    ax = axes[0]
    esr = [float(metrics[a]["ESR"]) * 100 for a in ARCHS]
    lo = [float(metrics[a]["ESR_ci95_low"]) * 100 for a in ARCHS]
    hi = [float(metrics[a]["ESR_ci95_high"]) * 100 for a in ARCHS]
    x = np.arange(len(ARCHS))
    ax.bar(x, esr, color=[COLORS[a] for a in ARCHS], width=0.55,
           yerr=[[e - l for e, l in zip(esr, lo)], [h - e for e, h in zip(esr, hi)]],
           capsize=6, error_kw=dict(ecolor="black", lw=1.1))
    for i, a in enumerate(ARCHS):
        m = metrics[a]
        ax.text(i, esr[i] - 8, f"{m['success']}/{m['episodes']}", ha="center",
                color="white", fontweight="bold", fontsize=11)
        ax.text(i, esr[i] + 5.5, f"CI [{lo[i]:.1f}, {hi[i]:.1f}]", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(ARCHS, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("ESR (%)")
    ax.set_ylim(0, 108)
    ax.set_title("(a) Overall ESR（n=240 episodes/架构；Wilson 95% CI）")
    # (b) by difficulty
    ax = axes[1]
    w = 0.26
    for i, a in enumerate(ARCHS):
        vals = [float(diff_metrics[f"{d}:{a}"]["ESR"]) * 100 for d in DIFFS]
        ax.bar(np.arange(3) + (i - 1) * w, vals, width=w, color=COLORS[a], label=a)
        for j, v in enumerate(vals):
            ax.text(j + (i - 1) * w, v + 1.5, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(["short (2步)", "medium (5步)", "long (10步)"])
    ax.set_ylabel("ESR (%)")
    ax.set_ylim(0, 115)
    ax.set_title("(b) ESR × 难度分层（每格 n=80 episodes）")
    ax.legend(fontsize=8, loc="lower right")
    fig.suptitle("图1  P1 主实验：三架构任务成功率（ESR）总体与分层对比 — deepseek-v4.1-flash-1017", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_esr_overall_strata.png", dpi=160)
    plt.close(fig)
    print("wrote fig1_esr_overall_strata.png")


def fig2():
    """prompt_tokens/episode 分布（柱=均值，点=240 集实测；注 median/IQR）。"""
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(ARCHS))
    rng = np.random.default_rng(7)
    for i, a in enumerate(ARCHS):
        m = metrics[a]
        mean = float(m["prompt_mean"])
        ax.bar(i, mean, color=COLORS[a], width=0.5, zorder=1)
        vals = ep_prompt[a]
        pts = np.full(len(vals), i) + rng.uniform(-0.16, 0.16, len(vals))
        ax.scatter(pts, vals, s=9, color="black", alpha=0.35, zorder=2)
        ax.text(i, mean + 130,
                f"μ={mean:.0f}\nmedian={m['prompt_median']}\nIQR={m['prompt_iqr']}",
                ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ARCHS, rotation=12, ha="right", fontsize=10)
    ax.set_ylabel("prompt_tokens / episode（tokens）")
    ax.set_title("图2  prompt_tokens/episode 分布（柱=均值±标注 median/IQR，点=240 episode 实测）\n"
                 "主要上下文开销指标；max_tokens=2048；P1 冻结任务集")
    top = max(float(metrics[a]["prompt_max"]) for a in ARCHS)
    ax.set_ylim(0, top * 1.12)
    save(fig, "fig2_prompt_distribution.png")


def fig3():
    """ESR–Token 权衡（bootstrap CI 误差棒）。"""
    boot = list(csv.DictReader((HERE / "bootstrap_results.csv").open(encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for a in ARCHS:
        m = metrics[a]
        x = float(m["prompt_mean"])
        y = float(m["ESR"]) * 100
        br = [b for b in boot if b["scope"] == "architecture_point"
              and b["key"] == a and b["metric"] == "prompt_per_episode"][0]
        xlo, xhi = float(br["ci95_low"]), float(br["ci95_high"])
        ylo, yhi = float(m["ESR_ci95_low"]) * 100, float(m["ESR_ci95_high"]) * 100
        ax.errorbar(x, y, xerr=[[x - xlo], [xhi - x]], yerr=[[y - ylo], [yhi - y]],
                    fmt="o", color=COLORS[a], markersize=11, capsize=5,
                    label=f"{a} (TPAE={float(m['TPAE']):.0f})")
        ax.annotate(a, (x, y), textcoords="offset points", xytext=(9, -4),
                    fontsize=9, color=COLORS[a])
    ax.set_xlabel("平均 prompt_tokens / episode（tokens；task-cluster bootstrap 95% CI）")
    ax.set_ylabel("ESR（%；Wilson 95% CI）")
    ax.set_title("图3  能力–开销权衡（每点=一架构；n=240/架构）\n"
                 "左方更省：vam_coder_v1.2_F 与两个非 VAM 架构 ESR 重叠、prompt 显著更低")
    ax.set_ylim(84, 102)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower left")
    save(fig, "fig3_tradeoff.png")


def fig4():
    """上下文增长曲线：long 任务按 step 序号的平均 prompt_tokens。"""
    by_step = defaultdict(list)
    for r in raw:
        if r["difficulty"] == "long":
            by_step[(r["architecture"], int(r["step"].replace("step", "")))].append(
                int(r["prompt_tokens"])
            )
    fig, ax = plt.subplots(figsize=(9, 5))
    for a in ARCHS:
        steps = sorted(s for (arch, s) in by_step if arch == a)
        means = [np.mean(by_step[(a, s)]) for s in steps]
        ax.plot(steps, means, marker="o", color=COLORS[a], label=a, lw=2)
        ax.annotate(f"step10={means[-1]:.0f}", (steps[-1], means[-1]),
                    textcoords="offset points", xytext=(-60, 6),
                    fontsize=8, color=COLORS[a])
    ax.set_xlabel("step 序号（long 任务 = 10 步）")
    ax.set_ylabel("该步平均 prompt_tokens（tokens）")
    ax.set_title("图4  Long 任务上下文增长曲线（每点每架构 n=16 tasks × R=5 = 80）\n"
                 "vam_coder_v1.2_F 全程位于非 VAM 架构下方 → 增长速度更慢")
    ax.set_xticks(range(1, 11))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    save(fig, "fig4_context_growth_long.png")


def fig5():
    """任务级配对差值（48 任务；F−memory_off 与 F−symbol_full_read）。"""
    tasks = sorted({k.split(":")[0] for k in task_metrics})
    d_mem = [float(task_metrics[f"{t}:vam_coder_v1.2_F"]["prompt_mean"])
             - float(task_metrics[f"{t}:memory_off"]["prompt_mean"]) for t in tasks]
    d_sym = [float(task_metrics[f"{t}:vam_coder_v1.2_F"]["prompt_mean"])
             - float(task_metrics[f"{t}:symbol_full_read"]["prompt_mean"]) for t in tasks]
    fig, ax = plt.subplots(figsize=(14, 5))
    w = 0.4
    x = np.arange(len(tasks))
    b1 = ax.bar(x - w / 2, d_mem, width=w, color=COLORS["memory_off"],
                label="Δprompt  vam_coder_v1.2_F − memory_off")
    b2 = ax.bar(x + w / 2, d_sym, width=w, color=COLORS["symbol_full_read"],
                label="Δprompt  vam_coder_v1.2_F − symbol_full_read")
    ax.axhline(0, color="black", lw=0.8)
    neg = sum(1 for v in d_mem + d_sym if v < 0)
    ax.text(0.99, 0.96, f"48 任务 ×2 对照 = 96 格中 {neg} 格为负（F 更省）",
            transform=ax.transAxes, ha="right", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("p1_", "") for t in tasks], rotation=60, ha="right",
                       fontsize=7)
    ax.set_ylabel("Δ 平均 prompt_tokens / episode（tokens，负值=F 更省）")
    ax.set_title("图5  任务级配对差值：vam_coder_v1.2_F 相对两个非 VAM 架构（逐任务，非总体均值）")
    ax.legend(fontsize=9)
    save(fig, "fig5_task_deltas.png")


def fig6():
    """失败机制堆叠（步级）。"""
    order = ["model_noop", "model_wrong_implementation", "model_no_edit",
             "protocol_violation", "infrastructure_error"]
    labels = {"model_noop": "model_noop", "model_wrong_implementation": "model_wrong_implementation",
              "model_no_edit": "model_no_edit", "protocol_violation": "protocol_violation",
              "infrastructure_error": "infrastructure_error"}
    counts = {a: Counter() for a in ARCHS}
    for fr in fails:
        for m in fr["mechanisms"].split(";"):
            if m:
                counts[fr["architecture"]][m] += 1
    fig, ax = plt.subplots(figsize=(9.5, 5))
    x = np.arange(len(ARCHS))
    bottom = np.zeros(len(ARCHS))
    palette = ["#8172B3", "#C44E52", "#937860", "#555555", "#DA8BC3"]
    for k, m in enumerate(order):
        vals = np.array([counts[a][m] for a in ARCHS], dtype=float)
        if vals.sum() == 0:
            continue
        ax.bar(x, vals, bottom=bottom, color=palette[k], label=labels[m])
        bottom += vals
    for i, a in enumerate(ARCHS):
        ax.text(i, bottom[i] + 0.5, f"失败集 {metrics[a]['episodes'] and (240 - int(metrics[a]['success']))}",
                ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ARCHS, rotation=12, ha="right", fontsize=10)
    ax.set_ylabel("失败机制计数（步级）")
    ax.set_title("图6  失败机制分布（47 个失败 episode 的步级分类；INSUFFICIENT/DHO=0）\n"
                 "max_tokens=2048；protocol 含触顶型截断，按预注册如实计入")
    ax.legend(fontsize=8)
    save(fig, "fig6_failure_mechanisms.png")


def fig7():
    """族级敏感性：8 任务族的 Δprompt（两个主对照）。"""
    fam_names = sorted({v["family"] for v in ep.values()})
    fam_diff_mem, fam_diff_sym = [], []
    for fam in fam_names:
        tks = sorted({v["task"] for v in ep.values() if v["family"] == fam})
        def fam_mean(arch):
            vals = [p for t in tks for p in ep_task_prompt[(t, arch)]]
            return float(np.mean(vals))
        fam_diff_mem.append(fam_mean("vam_coder_v1.2_F") - fam_mean("memory_off"))
        fam_diff_sym.append(fam_mean("vam_coder_v1.2_F") - fam_mean("symbol_full_read"))
    fig, ax = plt.subplots(figsize=(11, 5))
    w = 0.38
    x = np.arange(len(fam_names))
    ax.bar(x - w / 2, fam_diff_mem, width=w, color=COLORS["memory_off"],
           label="Δprompt  F − memory_off")
    ax.bar(x + w / 2, fam_diff_sym, width=w, color=COLORS["symbol_full_read"],
           label="Δprompt  F − symbol_full_read")
    ax.axhline(0, color="black", lw=0.8)
    for xi, (m_, s_) in enumerate(zip(fam_diff_mem, fam_diff_sym)):
        ax.text(xi - w / 2, m_ - 60, f"{m_:.0f}", ha="center", fontsize=7.5)
        ax.text(xi + w / 2, s_ - 60, f"{s_:.0f}", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f.replace("p1_", "") for f in fam_names], rotation=25,
                       ha="right", fontsize=9)
    ax.set_ylabel("Δ 平均 prompt_tokens / episode（tokens）")
    ax.set_title("图7  任务族敏感性：8 个参数化族的配对差值全部为负（F 更省）\n"
                 "family 聚类 sign-flip：p=0.0079 / 0.0072（预注册敏感性分析）")
    ax.legend(fontsize=9)
    save(fig, "fig7_family_sensitivity.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
    print("ALL DONE")
