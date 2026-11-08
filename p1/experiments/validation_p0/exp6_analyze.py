#!/usr/bin/env python
"""P0 实验6 分析：max_tokens 敏感性 → 触顶率 / protocol / ESR / token。

判定规则（prereg §7，开跑前锁定）：
  P1 主预算 = 使全部架构 protocol(触顶类)=0 的最小预算。
输出 exp6_summary.csv + 控制台判定。
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "exp6_max_tokens"
BUDGETS = [1024, 2048, 4096]
ARCHS = [
    "vam_coder_v1.2_E",
    "vam_coder_v1.2_F",
    "vam_coder_v1.3_V13B",
    "memory_off",
    "symbol_full_read",
]


def load_budget(b: int) -> list[dict]:
    """episode 级：success, trunc_steps, empty_steps, protocol_steps, tokens"""
    root = BASE / f"budget_{b}"
    eps: dict[str, dict] = {}
    for csv_path in root.glob("episode_logs/*/runner_out/per_step.csv"):
        ep_id = csv_path.parts[-3]
        with csv_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        e = eps.setdefault(ep_id, {
            "episode_id": ep_id, "budget": b, "success": True,
            "trunc": 0, "empty": 0, "protocol": 0,
            "prompt": 0, "completion": 0, "steps": len(rows),
        })
        for r in rows:
            e["success"] = e["success"] and r.get("eval_success") == "1"
            pt = int(r.get("prompt_tokens") or 0)
            ct = int(r.get("completion_tokens") or 0)
            e["prompt"] += pt
            e["completion"] += ct
            if ct >= b:
                e["trunc"] += 1
            # 空响应且非 INSUFFICIENT/dry → protocol 触顶类
            # （response 文件在 runner_out/episodes/.../steps/ 下，路径推导过重时用
            #  判定：ct==b 且 eval!=1 已覆盖触顶；显式 protocol 计数由 failure 机制补）
    return list(eps.values())


def count_protocol(root: Path, budget: int) -> dict[str, int]:
    """触顶型 protocol：completion >= budget 且可见输出无 FILE:/NO_EDIT（含空响应）。
    → {episode_id: 步数}"""
    import json
    out: dict[str, int] = defaultdict(int)
    for resp in root.glob("episode_logs/*/runner_out/episodes/*/*/steps/*/response.txt"):
        rj = resp.parent / "result.json"
        if not rj.exists():
            continue
        d = json.loads(rj.read_text(encoding="utf-8"))
        ct = int(d.get("completion_tokens") or 0)
        text = resp.read_text(encoding="utf-8")
        if ct >= budget and ("FILE:" not in text) and ("NO_EDIT" not in text):
            # response.txt ← step ← steps ← <arch> ← <task> ← episodes ← runner_out ← <ep_id>
            out[resp.parents[6].name] += 1
    return out


def arch_of(ep_id: str) -> str:
    for a in ARCHS:
        if f"_{a}_" in ep_id:
            return a
    raise ValueError(ep_id)


def main() -> int:
    rows = []
    decision = {}
    for b in BUDGETS:
        eps = load_budget(b)
        proto_eps = count_protocol(BASE / f"budget_{b}", b)
        for a in ARCHS:
            sel = [e for e in eps if arch_of(e["episode_id"]) == a]
            n = len(sel)
            succ = sum(int(e["success"]) for e in sel)
            trunc_steps = sum(e["trunc"] for e in sel)
            proto = sum(proto_eps.get(e["episode_id"], 0) for e in sel)
            prompt = sum(e["prompt"] for e in sel)
            comp = sum(e["completion"] for e in sel)
            rows.append({
                "budget": b, "architecture": a, "episodes": n,
                "success": succ, "ESR": f"{succ / n:.4f}",
                "trunc_steps_completion_ge_budget": trunc_steps,
                "protocol_empty_response_steps": proto,
                "prompt_tokens_total": prompt,
                "completion_tokens_total": comp,
                "completion_mean": f"{comp / max(1, sum(e['steps'] for e in sel)):.1f}",
            })
        # 判定用：该预算下全架构 protocol(触顶类) 合计
        total_proto = sum(r["protocol_empty_response_steps"] for r in rows if r["budget"] == b)
        total_trunc = sum(r["trunc_steps_completion_ge_budget"] for r in rows if r["budget"] == b)
        decision[b] = (total_proto, total_trunc)

    fields = ["budget", "architecture", "episodes", "success", "ESR",
              "trunc_steps_completion_ge_budget", "protocol_empty_response_steps",
              "prompt_tokens_total", "completion_tokens_total", "completion_mean"]
    with (HERE / "exp6_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print("=== exp6 per budget (all archs) ===")
    chosen = None
    for b in BUDGETS:
        proto, trunc = decision[b]
        ok = proto == 0
        print(f"budget={b}: protocol(空响应)={proto} 触顶步(completion>=budget)={trunc} "
              f"→ {'PASS' if ok else 'FAIL'}")
        if ok and chosen is None:
            chosen = b
    print(f"\n判定（prereg §7）：P1 主预算 = {chosen}")
    print("\n=== per budget × architecture ===")
    for r in rows:
        print(f"  {r['budget']} {r['architecture']:24s} ESR={r['ESR']} "
              f"trunc={r['trunc_steps_completion_ge_budget']} "
              f"proto={r['protocol_empty_response_steps']} "
              f"C_mean={r['completion_mean']}")
    with (HERE / "exp6_decision.txt").open("w", encoding="utf-8") as f:
        f.write(f"P1_main_budget={chosen}\n")
        for b in BUDGETS:
            proto, trunc = decision[b]
            f.write(f"budget={b} protocol_empty={proto} trunc_steps={trunc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
