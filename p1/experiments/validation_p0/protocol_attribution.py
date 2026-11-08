#!/usr/bin/env python
"""第5项（优先级表）：协议违规离线归因——跨 round1/2/3 + P1 + P2 统一重判。

判定（与 rev3 §4.5 protocol 类一致）：step 评测失败 且 无 runner error 且
响应既无 `FILE:` 也无 `NO_EDIT` → protocol 违规候选；再按触顶状态分类：
  - EMPTY_TRUNC   : completion >= budget 且可见输出为空（reasoning 烧尽预算）
  - TRUNC_NO_FILE : completion >= budget 且有输出但无合规块（截断在格式前/中）
  - FORMAT        : completion <  budget 且无合规块（真格式违规，未触顶）
预算按轮次：round1/2 = 1024；round3/P1/P2 = 2048。
输出 protocol_attribution.csv + 控制台透视表（供受控复测设计）。
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent          # p1/experiments/validation_p0
P1EXP = HERE.parent
ROOTS = [
    ("round1_holdout", P1EXP / "v13_holdout_validation" / "episode_logs", 1024),
    ("round2_v13b", P1EXP / "v13b_holdout_validation" / "episode_logs", 1024),
    ("round3_deepseek", P1EXP / "round3_deepseek_flash" / "episode_logs", 1024),
    ("p1_confirmatory", P1EXP / "p1_validation" / "episode_logs", 2048),
    ("p2_ablation", P1EXP / "p2_ablation" / "episode_logs", 2048),
]


def classify(text: str, ct: int, budget: int) -> str | None:
    has_file, has_noedit = "FILE:" in text, "NO_EDIT" in text
    if has_file or has_noedit:
        return None
    if ct >= budget:
        return "EMPTY_TRUNC" if not text.strip() else "TRUNC_NO_FILE"
    return "FORMAT"


def main() -> int:
    rows = []
    scanned = 0
    for round_name, root, budget in ROOTS:
        if not root.exists():
            print(f"skip missing root: {root}")
            continue
        for rj in root.glob("*/runner_out/episodes/*/*/steps/*/result.json"):
            scanned += 1
            try:
                d = json.loads(rj.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if d.get("eval_success") == "1":
                continue
            err = d.get("error") or ""
            if err and "dry_run" not in err:
                continue
            resp_p = rj.parent / "response.txt"
            text = resp_p.read_text(encoding="utf-8") if resp_p.exists() else ""
            cls = classify(text, int(d.get("completion_tokens") or 0), budget)
            if cls is None:
                continue
            # result.json 路径 = .../episode_logs/<ep>/runner_out/episodes/<task>/<arch>/steps/<step>/result.json
            ep_id = rj.parts[rj.parts.index("episode_logs") + 1]
            rows.append({
                "round": round_name,
                "episode_id": ep_id,
                "task_id": d.get("episode", ""),
                "architecture": next((a for a in (
                    "vam_coder_v1.2_F_ablate_history_redact",
                    "vam_coder_v1.2_F_ablate_no_must_closure",
                    "vam_coder_v1.2_F_ablate_no_oprime",
                    "vam_coder_v1.2_E_ablate_no_must_closure",
                    "vam_coder_v1.3_V13B", "vam_coder_v1.2_F",
                    "vam_coder_v1.2_E", "vam_coder_v1.2_H",
                    "memory_off", "symbol_full_read",
                ) if f"_{a}_" in ep_id), "?"),
                "step": d.get("step", ""),
                "budget": budget,
                "prompt_tokens": d.get("prompt_tokens", 0),
                "completion_tokens": d.get("completion_tokens", 0),
                "response_len": len(text),
                "eval_success": d.get("eval_success", ""),
                "class": cls,
                "response_path": str(resp_p),
            })

    fields = ["round", "episode_id", "task_id", "architecture", "step", "budget",
              "prompt_tokens", "completion_tokens", "response_len", "eval_success",
              "class", "response_path"]
    out = HERE / "protocol_attribution.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"scanned steps={scanned}, protocol violations={len(rows)}")
    print("\n=== by round × class ===")
    piv = Counter((r["round"], r["class"]) for r in rows)
    classes = ["EMPTY_TRUNC", "TRUNC_NO_FILE", "FORMAT"]
    print(f"{'round':22s}" + "".join(f"{c:>16s}" for c in classes))
    for rd in sorted({k[0] for k in piv}):
        print(f"{rd:22s}" + "".join(f"{piv[(rd, c)]:>16d}" for c in classes))
    print("\n=== by budget × class ===")
    pb = Counter((r["budget"], r["class"]) for r in rows)
    for b in sorted({k[0] for k in pb}):
        print(f"budget={b}: " + ", ".join(f"{c}={pb[(b, c)]}" for c in classes))
    print("\n=== by architecture × class (top) ===")
    pa = Counter((r["architecture"], r["class"]) for r in rows)
    for (a, c), n in pa.most_common(15):
        print(f"  {a:48s} {c:14s} {n}")
    # 非触顶 FORMAT 明细（真格式违规，复测重点）
    fmt = [r for r in rows if r["class"] == "FORMAT"]
    print(f"\nFORMAT (未触顶真格式违规) = {len(fmt)}; EMPTY_TRUNC = "
          f"{sum(1 for r in rows if r['class']=='EMPTY_TRUNC')}; "
          f"TRUNC_NO_FILE = {sum(1 for r in rows if r['class']=='TRUNC_NO_FILE')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
