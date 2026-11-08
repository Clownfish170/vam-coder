#!/usr/bin/env python
"""双 Token 专项分析（补记 v1 冻结口径 §4/§5）。

假设：H-B（B−D prompt↓ 且 ESR 非劣 −12pp）、H-C（C−D 同）、H-AB（C−B 分离两成分方向）。
指标：prompt/completion 分列、ESR/SPR、Peak Context、Context Growth Rate（OLS 斜率）、
Redundant Token Ratio（同 sha 重发块，chars/4 估计为 token，披露）、
Retrieval Overhead（SYMBOL/SYMBOL_SOURCE/STATIC 标记块 chars/4）、
Latency（t_model_ms/t_step_ms）、CMR（CIRE 口径：context 主 + visible 次）。
统计：task 级配对，bootstrap seed=20261102 B=10000 cluster=task_id，
sign-flip B=10000，主比较 B−D/C−D 各 Holm；非劣 margin −12pp。
四组同模型同 tokenizer，组间可比；不跨模型合并。
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]
TASKS_JSON = P1 / "tasks_p1_validation" / "p1_tasks.json"
LOGS = HERE / "episode_logs"
EXEC_LOG = HERE / "execution_log.jsonl"

ARMS = [
    "dualtoken_A_inline_full_context",
    "dualtoken_B_symbolic_addressing",
    "dualtoken_C_static_rep_plus_symbolic_id",
    "vam_coder_v1.2_F",
]
D_REF = "vam_coder_v1.2_F"
PRIMARY = [("dualtoken_B_symbolic_addressing", D_REF),
           ("dualtoken_C_static_rep_plus_symbolic_id", D_REF)]
SECONDARY = [("dualtoken_A_inline_full_context", D_REF),
             ("dualtoken_C_static_rep_plus_symbolic_id", "dualtoken_B_symbolic_addressing")]
NI_MARGIN = -0.12
B_SEED, B_BOOT, B_FLIP = 20261102, 10000, 10000
CHARS_PER_TOKEN = 4  # 与运行 config chars_per_token 一致（披露）
MARKER_RE = re.compile(r"--- (?:SYMBOL|SYMBOL_SOURCE|STATIC) ")
BLOCK_SPLIT_RE = re.compile(r"\n(?=--- (?:FILE|INDEX|SYMBOL|SYMBOL_SOURCE|STATIC) |=== )")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def arch_of(ep_id: str):
    for a in sorted(ARMS, key=len, reverse=True):
        if f"_{a}_" in ep_id:
            return a
    return None


def ols_slope(ys: list[float]) -> float:
    n = len(ys)
    if n < 2:
        return float("nan")
    xs = np.arange(n, dtype=float)
    xm, ym = xs.mean(), np.mean(ys)
    denom = ((xs - xm) ** 2).sum()
    if denom == 0:
        return float("nan")
    return float(((xs - xm) * (ys - ym)).sum() / denom)


def load_episodes():
    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    meta = {e["id"]: e for e in tasks_doc["episodes"]}
    info_by_task = {e["id"]: e["required_info_points"] for e in tasks_doc["episodes"]}
    eps = {}
    for ep_dir in sorted(LOGS.iterdir()):
        if not ep_dir.is_dir():
            continue
        ep_id = ep_dir.name
        arch = arch_of(ep_id)
        if arch is None:
            continue
        core, rep_s = ep_id.rsplit("_R", 1)
        task = next((t for t in meta if core.startswith(t + "_")), None)
        if task is None:
            continue
        step_dirs = sorted(
            (ep_dir / "runner_out" / "episodes" / task).glob("*/steps/step*"),
            key=lambda p: int(p.name.replace("step", "")),
        )
        if not step_dirs:
            continue
        steps = []
        for sd in step_dirs:
            rj = sd / "result.json"
            if not rj.exists():
                continue
            d = json.loads(rj.read_text(encoding="utf-8"))
            ctx = (sd / "context.txt").read_text(encoding="utf-8") if (sd / "context.txt").exists() else ""
            msgs = json.loads((sd / "messages.json").read_text(encoding="utf-8")) if (sd / "messages.json").exists() else []
            user = msgs[-1]["content"] if msgs else ""
            hist = "\n".join(m.get("content", "") for m in msgs[:-1])
            steps.append({
                "step": sd.name, "idx": int(sd.name.replace("step", "")),
                "result": d, "context": ctx, "user": user, "history": hist,
            })
        eps[ep_id] = {
            "episode_id": ep_id, "task_id": task, "architecture": arch,
            "rep": int(rep_s), "family": meta[task]["family"],
            "difficulty": meta[task]["difficulty"], "steps": steps,
        }
    return eps, info_by_task, meta


def make_matcher(value: str):
    if len(value) < 4:
        pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])")
        return lambda text: bool(pat.search(text))
    v = value
    return lambda text: v in text


def episode_metrics(e) -> dict:
    steps = e["steps"]
    succ = all(s["result"].get("eval_success") == 1 for s in steps)
    prompt = sum(int(s["result"].get("prompt_tokens") or 0) for s in steps)
    comp = sum(int(s["result"].get("completion_tokens") or 0) for s in steps)
    peak = max((int(s["result"].get("prompt_tokens") or 0) for s in steps), default=0)
    slope = ols_slope([int(s["result"].get("prompt_tokens") or 0) for s in steps])
    # Redundant Token Ratio：同 sha 文件块重发（chars/4 估计）
    seen: set[str] = set()
    red_chars = 0
    ctx_chars_total = 0
    # Retrieval Overhead：寻址/静态标记块 chars
    ret_chars = 0
    for s in steps:
        ctx = s["context"]
        ctx_chars_total += len(ctx)
        # 文件块（带内容的 FILE 块）
        pos = [m.start() for m in re.finditer(r"(?m)^--- FILE ", ctx)]
        for i, st in enumerate(pos):
            end = pos[i + 1] if i + 1 < len(pos) else len(ctx)
            seg = ctx[st:end]
            # 块内容 = 首行之后
            body = seg.split("\n", 1)[1] if "\n" in seg else ""
            h = sha256_text(body)
            if h in seen:
                red_chars += len(seg)
            else:
                seen.add(h)
        # 寻址开销块
        for m in MARKER_RE.finditer(ctx):
            st = m.start()
            nxt = re.search(r"\n(?=--- (?:FILE|INDEX|SYMBOL|SYMBOL_SOURCE|STATIC) |=== )", ctx[st + 1:])
            end = st + 1 + nxt.start() if nxt else len(ctx)
            ret_chars += end - st
    return {
        "episode_id": e["episode_id"], "task_id": e["task_id"],
        "architecture": e["architecture"], "rep": e["rep"],
        "family": e["family"], "difficulty": e["difficulty"],
        "success": int(succ), "steps": len(steps),
        "steps_passed": sum(1 for s in steps if s["result"].get("eval_success") == 1),
        "prompt_tokens": prompt, "completion_tokens": comp,
        "total_tokens": prompt + comp, "peak_context": peak,
        "growth_slope": slope,
        "rtr": (red_chars / ctx_chars_total) if ctx_chars_total else float("nan"),
        "retrieval_overhead_tok": ret_chars / CHARS_PER_TOKEN,
        "t_model_ms": sum(float(s["result"].get("t_model_ms") or 0) for s in steps),
        "t_step_ms": sum(float(s["result"].get("t_step_ms") or 0) for s in steps),
        "insufficient_steps": sum(int(s["result"].get("insufficient") or 0) for s in steps),
    }


def cmr_rows(eps, info_by_task):
    rows = []
    for ep_id, e in sorted(eps.items()):
        points = info_by_task.get(e["task_id"], [])
        for s in e["steps"]:
            idx = s["idx"]
            ctx, user, hist = s["context"], s["user"], s["history"]
            for p in points:
                if idx not in p.get("needed_by_steps", []):
                    continue
                m = make_matcher(str(p["value"]))
                rows.append({
                    "episode_id": ep_id, "task_id": e["task_id"],
                    "architecture": e["architecture"], "step": s["step"],
                    "point_id": p["id"], "type": p["type"],
                    "redundant": int(bool(p.get("redundant_in_instruction"))),
                    "in_context": int(m(ctx)),
                    "in_visible": int(m(ctx) or m(user) or m(hist)),
                })
    return rows


def dist(vals):
    a = np.asarray([v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))],
                   dtype=float)
    if a.size == 0:
        return {"mean": "NA", "sd": "NA", "median": "NA", "iqr": "NA"}
    q1, q3 = np.percentile(a, [25, 75])
    return {"mean": f"{a.mean():.4f}",
            "sd": f"{a.std(ddof=1):.4f}" if a.size > 1 else "NA",
            "median": f"{np.median(a):.4f}", "iqr": f"{q3 - q1:.4f}"}


def signflip_p(diffs, signs):
    obs = abs(diffs.mean())
    null = np.abs((signs * diffs[None, :]).mean(axis=1))
    return float((np.sum(null >= obs) + 1) / (B_FLIP + 1))


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)
        out[k] = running
    return out


def main() -> int:
    eps, info_by_task, meta = load_episodes()
    print(f"episodes loaded: {len(eps)}")
    assert len(eps) == 960, len(eps)

    em = {k: episode_metrics(v) for k, v in eps.items()}
    with (HERE / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(em.values())[0].keys())
        w.writeheader()
        w.writerows(em.values())

    # ---- metrics summary
    metric_cols = ["success", "prompt_tokens", "completion_tokens", "total_tokens",
                   "peak_context", "growth_slope", "rtr", "retrieval_overhead_tok",
                   "t_model_ms", "t_step_ms"]
    rows_m = []
    by_arch = defaultdict(list)
    for m in em.values():
        by_arch[m["architecture"]].append(m)
    for a in ARMS:
        sel = by_arch[a]
        row = {"architecture": a, "episodes": len(sel),
               "ESR": f"{np.mean([x['success'] for x in sel]):.4f}"}
        for c in metric_cols[1:]:
            row[c] = dist([x[c] for x in sel])["mean"]
            row[c + "_median"] = dist([x[c] for x in sel])["median"]
        # 难度分层 ESR/prompt
        for d in ("short", "medium", "long"):
            sd = [x for x in sel if x["difficulty"] == d]
            row[f"ESR_{d}"] = f"{np.mean([x['success'] for x in sd]):.4f}"
            row[f"prompt_{d}"] = f"{np.mean([x['prompt_tokens'] for x in sd]):.1f}"
        rows_m.append(row)
    with (HERE / "metrics_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_m[0].keys()))
        w.writeheader()
        w.writerows(rows_m)

    # ---- CMR（CIRE 口径）
    crows = cmr_rows(eps, info_by_task)
    with (HERE / "cire_step_delivery.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(crows[0].keys()))
        w.writeheader()
        w.writerows(crows)
    rows_c = []
    for a in ARMS:
        sel = [r for r in crows if r["architecture"] == a]
        if not sel:
            continue
        rows_c.append({
            "architecture": a, "point_steps": len(sel),
            "CMR_context": f"{np.mean([r['in_context'] for r in sel]):.4f}",
            "CMR_visible_secondary": f"{np.mean([r['in_visible'] for r in sel]):.4f}",
            "CMR_context_redundant": (
                f"{np.mean([r['in_context'] for r in sel if r['redundant']]):.4f}"
                if any(r["redundant"] for r in sel) else "NA"),
            "CMR_context_hidden": (
                f"{np.mean([r['in_context'] for r in sel if not r['redundant']]):.4f}"
                if any(not r["redundant"] for r in sel) else "NA"),
        })
    with (HERE / "cire_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_c[0].keys()))
        w.writeheader()
        w.writerows(rows_c)

    # ---- task 级配对统计
    task_ids = sorted({m["task_id"] for m in em.values()})
    by_ta = defaultdict(list)
    for m in em.values():
        by_ta[(m["task_id"], m["architecture"])].append(m)

    def task_mean(t, a, key):
        return float(np.mean([x[key] for x in by_ta[(t, a)]]))

    rng = np.random.default_rng(B_SEED)
    pairs = PRIMARY + SECONDARY
    metric_names = ["prompt_tokens", "ESR_proxy", "peak_context", "growth_slope",
                    "rtr", "retrieval_overhead_tok", "total_tokens"]

    def stats_for(sample, a):
        out = {}
        out["prompt_tokens"] = np.mean([task_mean(t, a, "prompt_tokens") for t in sample])
        out["ESR_proxy"] = np.mean([task_mean(t, a, "success") for t in sample])
        out["peak_context"] = np.mean([task_mean(t, a, "peak_context") for t in sample])
        out["growth_slope"] = np.nanmean([task_mean(t, a, "growth_slope") for t in sample])
        out["rtr"] = np.nanmean([task_mean(t, a, "rtr") for t in sample])
        out["retrieval_overhead_tok"] = np.mean(
            [task_mean(t, a, "retrieval_overhead_tok") for t in sample])
        out["total_tokens"] = np.mean([task_mean(t, a, "total_tokens") for t in sample])
        return out

    boot = {(p, m): [] for p in pairs for m in metric_names}
    for _ in range(B_BOOT):
        sample = rng.choice(task_ids, size=len(task_ids), replace=True).tolist()
        st = {a: stats_for(sample, a) for a in ARMS}
        for p in pairs:
            for m in metric_names:
                boot[(p, m)].append(st[p[0]][m] - st[p[1]][m])
    point = {a: stats_for(task_ids, a) for a in ARMS}

    rows_b = []
    for p in pairs:
        kind = "primary" if p in PRIMARY else "secondary"
        for m in metric_names:
            arr = np.asarray(boot[(p, m)], dtype=float)
            pt = point[p[0]][m] - point[p[1]][m]
            rows_b.append({
                "pair": f"{p[0]}−{p[1]}", "comparison_kind": kind, "metric": m,
                "point": f"{pt:.6f}",
                "ci95_low": f"{np.nanpercentile(arr, 2.5):.6f}",
                "ci95_high": f"{np.nanpercentile(arr, 97.5):.6f}",
                "n_bootstrap": B_BOOT, "seed": B_SEED, "cluster": "task_id",
            })
    with (HERE / "bootstrap_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_b[0].keys()))
        w.writeheader()
        w.writerows(rows_b)

    # sign-flip（prompt 与 ESR）
    rng2 = np.random.default_rng(B_SEED)
    rows_sf = []
    signs = rng2.choice([-1.0, 1.0], size=(B_FLIP, len(task_ids)))
    for p in pairs:
        kind = "primary" if p in PRIMARY else "secondary"
        d_pr = np.array([task_mean(t, p[0], "prompt_tokens") - task_mean(t, p[1], "prompt_tokens")
                         for t in task_ids])
        d_esr = np.array([task_mean(t, p[0], "success") - task_mean(t, p[1], "success")
                          for t in task_ids])
        rows_sf += [
            {"pair": f"{p[0]}−{p[1]}", "comparison_kind": kind,
             "metric": "prompt_per_episode", "test": "task_signflip",
             "stat": f"mean_diff={d_pr.mean():.2f}",
             "p_value": f"{signflip_p(d_pr, signs):.6f}", "seed": B_SEED},
            {"pair": f"{p[0]}−{p[1]}", "comparison_kind": kind,
             "metric": "ESR", "test": "task_signflip",
             "stat": f"mean_diff={d_esr.mean():.4f}",
             "p_value": f"{signflip_p(d_esr, signs):.6f}", "seed": B_SEED},
        ]
    for metric in ("prompt_per_episode", "ESR"):
        prim = {r["pair"]: float(r["p_value"]) for r in rows_sf
                if r["comparison_kind"] == "primary" and r["metric"] == metric}
        adj = holm(prim)
        for r in rows_sf:
            if r["metric"] == metric:
                r["p_holm_primary"] = (f"{adj[r['pair']]:.6f}"
                                       if r["comparison_kind"] == "primary" else "NA")
    for r in rows_sf:
        r.setdefault("p_holm_primary", "NA")
    with (HERE / "signflip_tests.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_sf[0].keys()))
        w.writeheader()
        w.writerows(rows_sf)

    # ---- 假设判定
    def ci(pair, metric):
        r = next(x for x in rows_b if x["pair"] == f"{pair[0]}−{pair[1]}" and x["metric"] == metric)
        return float(r["point"]), float(r["ci95_low"]), float(r["ci95_high"])

    def sf_p(pair, metric):
        r = next(x for x in rows_sf if x["pair"] == f"{pair[0]}−{pair[1]}"
                 and x["metric"] == metric)
        return float(r["p_value"]), r["p_holm_primary"]

    verdicts = {}
    for name, pair in (("H-B", PRIMARY[0]), ("H-C", PRIMARY[1])):
        pt, lo, hi = ci(pair, "prompt_tokens")
        p_raw, p_holm = sf_p(pair, "prompt_per_episode")
        _, elo, _ = ci(pair, "ESR_proxy")
        ni = elo > NI_MARGIN
        verdicts[name] = {
            "pair": f"{pair[0]}−{pair[1]}",
            "prompt_delta": pt, "prompt_ci": [lo, hi],
            "prompt_p": p_raw, "prompt_p_holm": p_holm,
            "prompt_lower": bool(hi < 0),
            "esr_delta_ci_low": elo, "noninferior": bool(ni),
            "supported": bool(hi < 0 and ni),
        }
    # H-AB：C−B 方向（静态表示的增量）
    pt_ab, lo_ab, hi_ab = ci(SECONDARY[1], "prompt_tokens")
    verdicts["H-AB"] = {
        "pair": "C−B", "prompt_delta": pt_ab, "prompt_ci": [lo_ab, hi_ab],
        "direction": "C>B (static rep adds tokens)" if pt_ab > 0 else "C<B",
        "separable": bool(lo_ab > 0 or hi_ab < 0),
    }

    manifest = {
        "schema": "dualtoken-analysis-v1",
        "generated_at": now(),
        "addendum_sha256": "d664d602fc3c82a9494c4eed7108e22f5ac272bff41ae732414ef3d60aa2a088",
        "episodes": len(eps), "tasks": len(task_ids),
        "bootstrap_seed": B_SEED, "bootstrap_B": B_BOOT, "signflip_B": B_FLIP,
        "cluster": "task_id", "ni_margin_esr": NI_MARGIN,
        "chars_per_token_disclosure": CHARS_PER_TOKEN,
        "rtr_method": "FILE 块 body sha256 跨步去重；比值按 chars（≈chars/4 token）",
        "retrieval_overhead_method": "--- SYMBOL/SYMBOL_SOURCE/STATIC 标记块 chars/4",
        "verdicts": verdicts,
        "outputs": ["episode_metrics.csv", "metrics_summary.csv", "bootstrap_results.csv",
                    "signflip_tests.csv", "cire_step_delivery.csv", "cire_summary.csv"],
    }
    (HERE / "dualtoken_analysis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdicts, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
