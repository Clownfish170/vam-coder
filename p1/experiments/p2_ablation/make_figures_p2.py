#!/usr/bin/env python
"""P2 图表：8 架构对比 + 机制森林 + CIRE + 失败机制（数据全部来自本次实验）。"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
F_BASE = "vam_coder_v1.2_F"
ARCHS = [
    F_BASE,
    "vam_coder_v1.2_E",
    "vam_coder_v1.2_H",
    "vam_coder_v1.2_F_ablate_no_must_closure",
    "vam_coder_v1.2_F_ablate_no_oprime",
    "vam_coder_v1.2_F_ablate_history_redact",
    "vam_coder_v1.3_V13B",
    "vam_coder_v1.2_E_ablate_no_must_closure",
]
SHORT = {
    F_BASE: "F\n(基准)",
    "vam_coder_v1.2_E": "E\n(digest消融)",
    "vam_coder_v1.2_H": "H\n(none消融)",
    "vam_coder_v1.2_F_ablate_no_must_closure": "F\n(无闭包)",
    "vam_coder_v1.2_F_ablate_no_oprime": "F\n(无O′)",
    "vam_coder_v1.2_F_ablate_history_redact": "F\n(redact历史)",
    "vam_coder_v1.3_V13B": "V13B\n(反例)",
    "vam_coder_v1.2_E_ablate_no_must_closure": "E\n(无闭包·交互)",
}
COLORS = {
    F_BASE: "#55A868",
    "vam_coder_v1.2_E": "#4C72B0",
    "vam_coder_v1.2_H": "#64B5CD",
    "vam_coder_v1.2_F_ablate_no_must_closure": "#FFC107",
    "vam_coder_v1.2_F_ablate_no_oprime": "#DD8452",
    "vam_coder_v1.2_F_ablate_history_redact": "#937860",
    "vam_coder_v1.3_V13B": "#8172B3",
    "vam_coder_v1.2_E_ablate_no_must_closure": "#C44E52",
}
metrics = {r["key"]: r for r in csv.DictReader((HERE / "metrics_summary.csv").open(encoding="utf-8"))
           if r["scope"] == "architecture"}
boot = list(csv.DictReader((HERE / "bootstrap_results.csv").open(encoding="utf-8")))
cire = {r["architecture"]: r for r in csv.DictReader((HERE / "cire_summary.csv").open(encoding="utf-8"))}

FIG.mkdir(exist_ok=True)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160)
    plt.close(fig)
    print("wrote", name)


def fig1():
    """ESR 8 架构。"""
    esr = [float(metrics[a]["ESR"]) * 100 for a in ARCHS]
    lo = [float(metrics[a]["ESR_ci95_low"]) * 100 for a in ARCHS]
    hi = [float(metrics[a]["ESR_ci95_high"]) * 100 for a in ARCHS]
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(ARCHS))
    ax.bar(x, esr, color=[COLORS[a] for a in ARCHS], width=0.6,
           yerr=[[e - l for e, l in zip(esr, lo)], [h - e for e, h in zip(esr, hi)]],
           capsize=5, error_kw=dict(ecolor="black", lw=1))
    for i, a in enumerate(ARCHS):
        m = metrics[a]
        ax.text(i, esr[i] - 7, f"{m['success']}/240", ha="center", color="white",
                fontweight="bold", fontsize=9)
        ax.text(i, esr[i] + 5.5, f"{esr[i]:.1f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[a] for a in ARCHS], fontsize=8)
    ax.set_ylabel("ESR (%)")
    ax.set_ylim(0, 110)
    ax.set_title("图1  P2 消融：8 架构任务成功率（ESR，Wilson 95% CI；n=240/架构）\n"
                 "深绿=基准 vam_coder_v1.2_F（P1 数据）；其余=7 个单开关消融/反例臂")
    save(fig, "fig1_esr_8arch.png")


def fig2():
    """prompt/episode 8 架构（柱+分布不可用跨根? episode 原始在两目录——用 metrics 均值+median 标注）。"""
    means = [float(metrics[a]["prompt_mean"]) for a in ARCHS]
    med = [float(metrics[a]["prompt_median"]) for a in ARCHS]
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(ARCHS))
    ax.bar(x, means, color=[COLORS[a] for a in ARCHS], width=0.6)
    for i, a in enumerate(ARCHS):
        ax.text(i, means[i] + 45, f"μ={means[i]:.0f}\nmed={med[i]:.0f}",
                ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[a] for a in ARCHS], fontsize=8)
    ax.set_ylabel("prompt_tokens / episode（tokens）")
    ax.set_ylim(0, max(means) * 1.28)
    ax.set_title("图2  P2 消融：平均 prompt_tokens/episode（柱=均值，标 median；n=240/架构）\n"
                 "F−无O′ = −398（O′ 复用每集省 398 tok）；F−redact = +350（脱敏历史更短，keep 反而贵 350）；其余 ≤±25")
    save(fig, "fig2_prompt_8arch.png")


def fig3():
    """机制森林：Δprompt 与 ΔESR（F − 消融）。"""
    pairs = [a for a in ARCHS if a != F_BASE]
    rows_p = [r for r in boot if r["scope"] == "paired_delta" and r["metric"] == "prompt_per_episode"]
    rows_e = [r for r in boot if r["scope"] == "paired_delta" and r["metric"] == "ESR"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    # prompt
    ax = axes[0]
    ys = np.arange(len(pairs))
    for i, a in enumerate(pairs):
        row = next(r for r in rows_p if r["key"] == f"{F_BASE}−{a}")
        pt, lo, hi = float(row["point"]), float(row["ci95_low"]), float(row["ci95_high"])
        col = COLORS[a]
        ax.errorbar(pt, i, xerr=[[pt - lo], [hi - pt]], fmt="o", color=col,
                    capsize=5, markersize=9)
        ax.text(hi + 18, i, f"{pt:+.0f}", va="center", fontsize=9)
    ax.axvline(0, color="black", lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([SHORT[a].replace("\n", " ") for a in pairs], fontsize=8.5)
    ax.set_xlabel("Δ prompt = F − 消融（负=F 更省=机制在省钱；正=消融更省=机制在花钱）")
    ax.set_title("(a) 机制的 prompt 贡献（bootstrap 95% CI）")
    ax.invert_yaxis()
    # ESR
    ax = axes[1]
    for i, a in enumerate(pairs):
        row = next(r for r in rows_e if r["key"] == f"{F_BASE}−{a}")
        pt, lo, hi = float(row["point"]) * 100, float(row["ci95_low"]) * 100, float(row["ci95_high"]) * 100
        col = COLORS[a]
        ax.errorbar(pt, i, xerr=[[pt - lo], [hi - pt]], fmt="o", color=col,
                    capsize=5, markersize=9)
        ax.text(hi + 0.6, i, f"{pt:+.1f}pp", va="center", fontsize=9)
    ax.axvline(0, color="black", lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([SHORT[a].replace("\n", " ") for a in pairs], fontsize=8.5)
    ax.set_xlabel("Δ ESR = F − 消融（pp；CI 全跨 0 = 无能力差异证据）")
    ax.set_title("(b) 机制的成功率贡献（bootstrap 95% CI）")
    ax.invert_yaxis()
    fig.suptitle("图3  单机制贡献森林图：Δ = vam_coder_v1.2_F − 各消融臂（n=240/架构）", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_mechanism_forest.png", dpi=160)
    plt.close(fig)
    print("wrote fig3_mechanism_forest.png")


def fig4():
    """CIRE：CMR_context / CMR_visible / IRR 三联。"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    x = np.arange(len(ARCHS))
    ctx = [float(cire[a]["CMR_context"]) for a in ARCHS]
    vis = [float(cire[a]["CMR_visible_secondary"]) for a in ARCHS]
    irr = [float(cire[a]["IRR_micro_file_units"]) for a in ARCHS]
    w = 0.38
    axes[0].bar(x - w / 2, ctx, width=w, color="#4C72B0", label="CMR_context（主口径）")
    axes[0].bar(x + w / 2, vis, width=w, color="#DD8452", label="CMR_visible（次要）")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([SHORT[a] for a in ARCHS], fontsize=7.5)
    axes[0].set_ylim(0, 1.05)
    axes[0].set_ylabel("CMR（比例）")
    axes[0].set_title("(a) 关键信息召回（144 信息点 × 需要步）")
    axes[0].legend(fontsize=8)
    # 隐藏点单独
    hid = [float(cire[a]["CMR_context_hidden"]) for a in ARCHS]
    red = [float(cire[a]["CMR_context_redundant"]) for a in ARCHS]
    axes[1].bar(x - w / 2, red, width=w, color="#90CAF9", label="指令冗余点")
    axes[1].bar(x + w / 2, hid, width=w, color="#E57373", label="隐藏点（仅文件/历史）")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([SHORT[a] for a in ARCHS], fontsize=7.5)
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title("(b) CMR_context 分解：冗余 vs 隐藏")
    axes[1].legend(fontsize=8)
    axes[2].bar(x, irr, color=[COLORS[a] for a in ARCHS], width=0.6)
    for i, v in enumerate(irr):
        axes[2].text(i, v + 0.015, f"{v:.2f}", ha="center", fontsize=8)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels([SHORT[a] for a in ARCHS], fontsize=7.5)
    axes[2].set_ylim(0, 0.85)
    axes[2].set_ylabel("IRR（无关注入/总注入，文件单元 micro）")
    axes[2].set_title("(c) 无关读取率（越低越干净）")
    fig.suptitle("图4  CIRE：关键信息召回与无关读取（预注册 §8；MEPR 归 P3=NA）", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_cire.png", dpi=160)
    plt.close(fig)
    print("wrote fig4_cire.png")


def fig5():
    """失败机制堆叠（8 架构）。"""
    order = ["model_noop", "model_wrong_implementation", "model_no_edit", "protocol_violation"]
    counts = {a: {} for a in ARCHS}
    for a in ARCHS:
        for m in order:
            counts[a][m] = int(metrics[a].get(f"fail_mech_{m}", 0) or 0)
    fig, ax = plt.subplots(figsize=(12, 5.2))
    x = np.arange(len(ARCHS))
    bottom = np.zeros(len(ARCHS))
    palette = ["#8172B3", "#C44E52", "#937860", "#555555"]
    for k, m in enumerate(order):
        vals = np.array([counts[a][m] for a in ARCHS], dtype=float)
        ax.bar(x, vals, bottom=bottom, color=palette[k], label=m)
        bottom += vals
    for i, a in enumerate(ARCHS):
        ax.text(i, bottom[i] + 0.7, f"{int(metrics[a]['failed_episodes'])} 集",
                ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[a] for a in ARCHS], fontsize=7.5)
    ax.set_ylabel("失败机制计数（步级）")
    ax.set_title("图5  P2 失败机制分布（步级；基准 F 的 17 集 = P1 分类；全臂 INSUFFICIENT/DHO=0）")
    ax.legend(fontsize=8)
    save(fig, "fig5_failures_8arch.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    print("ALL DONE")
