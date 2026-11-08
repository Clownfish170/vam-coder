#!/usr/bin/env python
"""就绪门检查（独立集预注册 §8）：前 36 集后只读评估，只停不调。

判定：
- 三臂 ESR 全为 0 或全为 1（完全地板/天花板）→ FAIL
- protocol 类失败率 > 20%（任一臂）→ FAIL
- infra 类失败率 > 20%（任一臂）→ FAIL
- 否则 PASS（继续全量）

用法：python readiness_gate.py [--episodes 36]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE / "episode_logs"
ARCHS = ["vam_coder_v1.2_F", "memory_off", "symbol_full_read"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=36)
    args = ap.parse_args()

    rows = []
    if (HERE / "execution_log.jsonl").exists():
        for line in (HERE / "execution_log.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if len(rows) < args.episodes:
        print(f"NOT READY: only {len(rows)}/{args.episodes} episodes logged")
        return 2

    # 取最早完成的 N 集（按日志顺序）
    head = rows[: args.episodes]
    per_arch = defaultdict(lambda: {"n": 0, "succ": 0, "protocol": 0, "infra": 0})
    for rec in head:
        a = rec["architecture"]
        per_arch[a]["n"] += 1
        # ESR：episode 级成功 = status OK 且 runner 记录全步通过
        # 用 runner_out/per_step.csv 判定（与分析脚本同口径）
        ep_dir = LOGS / rec["episode_id"] / "runner_out"
        ps = ep_dir / "per_step.csv"
        if rec.get("status") != "OK":
            # rc 类失败：区分 infra vs protocol 粗判
            if rec.get("rc") and "RC_" in str(rec.get("status")):
                per_arch[a]["infra"] += 1
            continue
        if not ps.exists():
            per_arch[a]["infra"] += 1
            continue
        with ps.open(newline="", encoding="utf-8") as f:
            srows = list(csv.DictReader(f))
        ok = all(r.get("eval_success") == "1" for r in srows)
        per_arch[a]["succ"] += int(ok)
        # protocol：空响应/触顶类 error（粗判，与 failure_analysis 同源字段）
        for r in srows:
            err = (r.get("error") or "").lower()
            if "insufficient" in err or "empty" in err or "trunc" in err:
                per_arch[a]["protocol"] += 1
                break

    print(f"readiness gate over first {len(head)} episodes:")
    problems = []
    esrs = []
    for a in ARCHS:
        m = per_arch[a]
        n = m["n"] or 1
        esr = m["succ"] / n
        esrs.append(esr)
        proto_rate = m["protocol"] / n
        infra_rate = m["infra"] / n
        print(f"  {a}: n={m['n']} ESR={esr:.3f} protocol_eps={m['protocol']} "
              f"infra_eps={m['infra']}")
        if proto_rate > 0.20:
            problems.append(f"{a}: protocol rate {proto_rate:.2f} > 0.20")
        if infra_rate > 0.20:
            problems.append(f"{a}: infra rate {infra_rate:.2f} > 0.20")
    if all(e == 0.0 for e in esrs):
        problems.append("all-arms ESR = 0 (floor)")
    if all(e == 1.0 for e in esrs):
        problems.append("all-arms ESR = 1 (ceiling)")

    if problems:
        print("GATE FAIL (stop and report, do not tune):")
        for p in problems:
            print("  -", p)
        return 1
    print("GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
