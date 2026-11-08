#!/usr/bin/env python
"""V1.3-M2 Holdout 图表（图1–图7）：全部来自本次实验原始记录，无平滑、无伪造。

输出：p1/experiments/v13_holdout_validation/figures/fig1..fig7.png
"""

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
ARMS = ["E", "F", "V13A"]
COLORS = {"E": "#4C72B0", "F": "#DD8452", "V13A": "#55A868"}

raw = list(csv.DictReader((HERE / "raw_results.csv").open(encoding="utf-8")))
metrics = list(csv.DictReader((HERE / "metrics_summary.csv").open(encoding="utf-8")))
boot = list(csv.DictReader((HERE / "bootstrap_results.csv").open(encoding="utf-8")))
fails = list(csv.DictReader((HERE / "failure_analysis.csv").open(encoding="utf-8")))
arm_metrics = {r["key"]: r for r in metrics if r["scope"] == "arm"}
task_metrics = {(r["key"].split(":")[0], r["key"].split(":")[1]): r for r in metrics if r["scope"] == "task_arm"}

# episode 级 prompt
ep_prompt: dict[tuple, list[int]] = defaultdict(list)
ep_success: dict[tuple, list[int]] = defaultdict(list)
for r in raw:
    key = (r["task_id"], r["arm"])
    # 同一 episode 的步要先聚合：按 episode_id 聚合
ep_by_id: dict[str, dict] = defaultdict(lambda: {"prompt": 0, "success": True, "task": "", "arm": ""})
for r in raw:
    e = ep_by_id[r["episode_id"]]
    e["prompt"] += int(r["prompt_tokens"])
    e["success"] = e["success"] and r["eval_success"] == "1"
    e["task"] = r["task_id"]
    e["arm"] = r["arm"]
for e in ep_by_id.values():
    ep_prompt[(e["task"], e["arm"])].append(e["prompt"])
    ep_success[(e["task"], e["arm"])].append(int(e["success"]))

FIG.mkdir(exist_ok=True)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160)
    plt.close(fig)
    print("wrote", name)


# ---------------- 图1：ESR 对比（柱状 + Wilson 95% CI + n）
def fig1():
    esr = [float(arm_metrics[a]["ESR"]) for a in ARMS]
    lo = [float(arm_metrics[a]["ESR_ci95_low"]) for a in ARMS]
    hi = [float(arm_metrics[a]["ESR_ci95_high"]) for a in ARMS]
    err = [[e - l for e, l in zip(esr, lo)], [h - e for e, h in zip(esr, hi)]]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(ARMS))
    bars = ax.bar(x, [e * 100 for e in esr], color=[COLORS[a] for a in ARMS], width=0.55, yerr=err, capsize=6,
                  error_kw=dict(ecolor="black", lw=1.2))
    for i, a in enumerate(ARMS):
        n = arm_metrics[a]["episodes"]
        k = arm_metrics[a]["success"]
        ax.text(i, float(arm_metrics[a]["ESR"]) * 100 + 4.5, f"{k}/{n}", ha="center", fontsize=10)
        ax.text(i, 1.2, f"CI [{lo[i]*100:.1f}, {hi[i]*100:.1f}]", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}\n(n={arm_metrics[a]['episodes']} episodes)" for a in ARMS])
    ax.set_ylabel("ESR 任务成功率 (%)（全步通过的 episode 比例）")
    ax.set_title("图1  E/F/V13A 任务成功率（ESR, %）对比\nWilson 95% CI；每臂 12 tasks × R=2 = 24 episodes；Qwen2.5-Coder-1.5B Q6_K")
    ax.set_ylim(0, 32)
    ax.axhline(0, color="black", lw=0.6)
    save(fig, "fig1_esr_comparison.png")


# ---------------- 图2：平均 prompt_tokens（柱 + 逐 episode 分布点）
def fig2():
    means = [float(arm_metrics[a]["prompt_tokens_mean_per_episode"]) for a in ARMS]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    x = np.arange(len(ARMS))
    ax.bar(x, means, color=[COLORS[a] for a in ARMS], width=0.5, zorder=1)
    rng = np.random.default_rng(7)
    for i, a in enumerate(ARMS):
        vals = [p for (t, aa), ps in ep_prompt.items() if aa == a for p in ps]
        pts = np.full(len(vals), i) + rng.uniform(-0.16, 0.16, len(vals))
        ax.scatter(pts, vals, s=14, color="black", alpha=0.55, zorder=2)
        ax.text(i, means[i] + 18, f"μ={means[i]:.1f}", ha="center", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}\n(n=24 eps)" for a in ARMS])
    ax.set_ylabel("prompt_tokens / episode（tokens）")
    ax.set_title("图2  各臂平均 prompt_tokens 对比（柱=均值，点=24 个 episode 实测分布）\nprompt_tokens=实际请求的完整 prompt 长度（主要上下文开销指标）")
    ax.set_ylim(0, max(max(m for m in means), 760) + 60)
    save(fig, "fig2_prompt_tokens.png")


# ---------------- 图3：ESR–Token 权衡散点
def fig3():
    fig, ax = plt.subplots(figsize=(7, 4.6))
    for a in ARMS:
        m = arm_metrics[a]
        x = float(m["prompt_tokens_mean_per_episode"])
        y = float(m["ESR"]) * 100
        lo = (y - float(m["ESR_ci95_low"]) * 100, float(m["ESR_ci95_high"]) * 100 - y)
        tp_lo = float([b for b in boot if b["scope"] == "arm_point" and b["key"] == a and b["metric"] == "prompt_per_episode"][0]["ci95_low"])
        tp_hi = float([b for b in boot if b["scope"] == "arm_point" and b["key"] == a and b["metric"] == "prompt_per_episode"][0]["ci95_high"])
        ax.errorbar(x, y, xerr=[[x - tp_lo], [tp_hi - x]], yerr=[[lo[0]], [lo[1]]],
                    fmt="o", color=COLORS[a], markersize=10, capsize=5, label=f"{a} (TPAE={float(m['TPAE']):.0f})")
        ax.annotate(a, (x, y), textcoords="offset points", xytext=(8, 6), fontsize=11, color=COLORS[a])
    ax.set_xlabel("平均 prompt_tokens / episode（tokens，横轴，含 task-cluster bootstrap 95% CI）")
    ax.set_ylabel("ESR 成功率（%，含 Wilson 95% CI）")
    ax.set_title("图3  成功率与 Token 开销权衡（每点=一个实验臂；n=24 episodes/臂）\n左下更优：更低上下文开销 + 更高成功率")
    ax.set_ylim(-3, 34)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=0.3)
    save(fig, "fig3_tradeoff.png")


# ---------------- 图4：各任务 Token 消耗对比（按 task_id）
def fig4():
    tasks = sorted({k[0] for k in task_metrics})
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    w = 0.26
    x = np.arange(len(tasks))
    for i, a in enumerate(ARMS):
        vals = [float(task_metrics[(t, a)]["prompt_tokens_mean_per_episode"]) for t in tasks]
        ax.bar(x + (i - 1) * w, vals, width=w, color=COLORS[a], label=a)
    # 标注任务级成功（全部任务：每臂 2 reps）
    for j, t in enumerate(tasks):
        succ = sum(ep_success[(t, "E")])
        ax.text(j, 8, "✓" if succ == 2 else "✗", ha="center", fontsize=9,
                color="green" if succ == 2 else "red")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("v13_", "") for t in tasks], rotation=30, ha="right")
    ax.set_ylabel("平均 prompt_tokens / episode（tokens）")
    ax.set_xlabel("task_id（✓=该任务 E 臂 2/2 成功，✗=0/2；三臂成功模式一致）")
    ax.set_title("图4  各任务 prompt_tokens 消耗对比（E/F/V13A，按 task_id，每任务 n=2 episodes/臂）")
    ax.legend(title="臂")
    save(fig, "fig4_tokens_by_task.png")


# ---------------- 图5：失败原因分布（堆叠柱，步级机制）
def fig5():
    mech_order = ["model_noop", "model_wrong_implementation", "model_no_edit", "protocol_violation", "infrastructure_error", "insufficient_no_request"]
    labels = {
        "model_noop": "模型无操作（输出文件未改动）",
        "model_wrong_implementation": "模型改了但实现错误",
        "model_no_edit": "模型返回 NO_EDIT",
        "protocol_violation": "协议违规（非 FILE/NO_EDIT）",
        "infrastructure_error": "基础设施错误",
        "insufficient_no_request": "INSUFFICIENT（未发请求）",
    }
    counts = {a: Counter() for a in ARMS}
    for fr in fails:
        for mech in fr["mechanisms"].split(";"):
            if mech:
                counts[fr["arm"]][mech] += 1
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    x = np.arange(len(ARMS))
    bottom = np.zeros(len(ARMS))
    palette = ["#8172B3", "#C44E52", "#937860", "#555555", "#DA8BC3", "#8C8C8C"]
    for k, mech in enumerate(mech_order):
        vals = np.array([counts[a][mech] for a in ARMS], dtype=float)
        if vals.sum() == 0:
            continue
        ax.bar(x, vals, bottom=bottom, color=palette[k % len(palette)], label=labels[mech])
        bottom += vals
    for i, a in enumerate(ARMS):
        ax.text(i, bottom[i] + 0.8, f"合计失败步 {int(bottom[i])}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}\n(n=24 eps)" for a in ARMS])
    ax.set_ylim(0, 44)
    ax.set_ylabel("失败机制计数（步级，来自失败 episode）")
    ax.set_title("图5  各臂失败原因分布（步级机制分类；每臂 48 步中 32 步失败）\n错误分类（rev3 §4.5）：协议 0 / 基础设施 0 / 架构 0 —— 全部为模型能力型失败")
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    save(fig, "fig5_failure_mechanisms.png")


# ---------------- 图6：记忆注入策略分析（Full/Digest/None + must + 升级）
def fig6():
    # 从 audit 级别数据：raw 的 blocks/digest/reuse + 需要 NONE → 从 audits 读
    acts = {a: Counter() for a in ARMS}
    must_n = {a: 0 for a in ARMS}
    steps_n = {a: 0 for a in ARMS}
    related_full = {a: [0, 0] for a in ARMS}
    adaptive_reason = Counter()
    for ep in (HERE / "episode_logs").iterdir():
        if not ep.is_dir():
            continue
        task = ep.name.rsplit("_R", 1)[0]
        arm = "V13A" if task.endswith("_V13A") else task.rsplit("_", 1)[-1]
        task_id = task[: -(len(arm) + 1)]
        aud = ep / "runner_out" / "episodes" / task_id / ("vam_coder_v1.3_V13A" if arm == "V13A" else f"vam_coder_v1.2_{arm}") / "logs" / "injection_audit.jsonl"
        if not aud.exists():
            continue
        for line in aud.read_text(encoding="utf-8").splitlines():
            a = json.loads(line)
            steps_n[arm] += 1
            for c in a["checks"]:
                acts[arm][c["action"]] += 1
            must_n[arm] += int(a["plan"].get("must_full_count", 0))
            lv = a["levels"]
            rf = sum(1 for x in lv if x["r"] >= 1 and x["level"] == "FULL")
            rn = sum(1 for x in lv if x["r"] >= 1)
            related_full[arm][0] += rf
            related_full[arm][1] += rn
            for row in a["plan"].get("adaptive_audit", []) or []:
                reason = row.get("reason") or ""
                if row.get("level") == "FULL":
                    key = "升级 Full（instruction_hit）"
                elif "no_implementation_body" in reason:
                    key = "Digest（仅常量、无实现体）"
                else:
                    key = "Digest（有实现体但无命中）"
                adaptive_reason[key] += 1

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    # (a) 注入动作分布（每步平均文件数）
    x = np.arange(len(ARMS))
    order = [("EXPAND", "Full（EXPAND）", "#4C72B0"), ("DIGEST", "Digest（INDEX 行）", "#DD8452"),
             ("REUSE_KV", "O′ 复用省略", "#55A868"), ("NONE", "None（未注入）", "#B0B0B0")]
    bottom = np.zeros(len(ARMS))
    for key, lab, col in order:
        vals = np.array([acts[a][key] / steps_n[a] for a in ARMS])
        axes[0].bar(x, vals, bottom=bottom, color=col, label=lab)
        bottom += vals
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(ARMS)
    axes[0].set_ylabel("文件数 / 步（均值）")
    axes[0].set_title("(a) 上下文注入动作分布（按步均值）")
    axes[0].legend(fontsize=7)

    # (b) must_full 与 related Full 比率（S7 描述性）
    must_mean = [must_n[a] / steps_n[a] for a in ARMS]
    axes[1].bar(x, must_mean, color="#8172B3", width=0.5, label="must_full 数/步")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(ARMS)
    axes[1].set_ylabel("must_full 文件数 / 步")
    ax2 = axes[1].twinx()
    ratios = [related_full[a][0] / related_full[a][1] if related_full[a][1] else 0 for a in ARMS]
    ax2.plot(x, ratios, "ko-", label="related→Full 比率（S7 描述）")
    for i, r in enumerate(ratios):
        ax2.text(i, r + 0.03, f"{r:.0%}", ha="center", fontsize=9)
    ax2.set_ylim(0, 1.25)
    ax2.set_ylabel("related 文件被置 Full 的比率")
    axes[1].set_title("(b) must_full 与 related→Full 比率（S7 描述，无假设检验）")
    h1, l1 = axes[1].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axes[1].legend(h1 + h2, l1 + l2, fontsize=7)

    # (c) V13A adaptive 决策原因
    keys = sorted(adaptive_reason, reverse=True)
    vals = [adaptive_reason[k] for k in keys]
    axes[2].barh(range(len(keys)), vals, color="#55A868")
    axes[2].set_yticks(range(len(keys)))
    axes[2].set_yticklabels(keys, fontsize=8)
    axes[2].set_xlabel("adaptive_audit 行数（文件×步，2 reps 汇总）")
    axes[2].set_title("(c) V13A adaptive 决策（10 行）")
    axes[2].set_xlim(0, 9.5)
    fig.suptitle("图6  记忆注入策略分析：Full / Digest / None 分布、must_full 与 V13A 升级率（原始审计记录）", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "fig6_injection_strategy.png", dpi=160)
    plt.close(fig)
    print("wrote fig6_injection_strategy.png")


# ---------------- 图7：任务级配对差值（V13A 相对 E / F）
def fig7():
    tasks = sorted({k[0] for k in task_metrics})
    d_e = [float(task_metrics[(t, "V13A")]["prompt_tokens_mean_per_episode"]) - float(task_metrics[(t, "E")]["prompt_tokens_mean_per_episode"]) for t in tasks]
    d_f = [float(task_metrics[(t, "V13A")]["prompt_tokens_mean_per_episode"]) - float(task_metrics[(t, "F")]["prompt_tokens_mean_per_episode"]) for t in tasks]
    ds_e = [sum(ep_success[(t, "V13A")]) - sum(ep_success[(t, "E")]) for t in tasks]
    ds_f = [sum(ep_success[(t, "V13A")]) - sum(ep_success[(t, "F")]) for t in tasks]
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    w = 0.38
    x = np.arange(len(tasks))
    b1 = ax.bar(x - w / 2, d_e, width=w, color="#55A868", label="Δprompt V13A−E")
    b2 = ax.bar(x + w / 2, d_f, width=w, color="#8172B3", label="Δprompt V13A−F")
    for bars in (b1, b2):
        for rect in bars:
            h = rect.get_height()
            if abs(h) >= 0.5:
                ax.text(rect.get_x() + rect.get_width() / 2, h + (1.5 if h >= 0 else -4.5),
                        f"{h:+.0f}", ha="center", fontsize=7.5)
    for j, t in enumerate(tasks):
        de, df = ds_e[j], ds_f[j]
        mark = "Δ成功 0" if de == 0 and df == 0 else f"Δ成功 {de:+d}/{df:+d}"
        ax.text(j, -52, mark, ha="center", fontsize=7, color="#333333")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("v13_", "") for t in tasks], rotation=30, ha="right")
    ax.set_ylabel("Δ 平均 prompt_tokens / episode（tokens，V13A−对照）")
    ax.set_title("图7  任务级配对差值：V13A 相对 E 和 F 的逐任务 Token 变化（非总体均值）\n每任务 n=2 episodes/臂；任务级 ΔESR 标注于轴下（本次全部为 0）")
    ax.legend()
    ax.set_ylim(-70, max(max(d_e + d_f) + 25, 40))
    save(fig, "fig7_task_deltas.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
    print("ALL FIGURES DONE")
