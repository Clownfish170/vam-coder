#!/usr/bin/env python
"""只读导出 P1-v1.0 正式实验的 P2 输入数据（不调用模型、不修改 run）。

输出：p1/results/p2_input/{formal_runs.csv, usage_summary.json, data_dictionary.md}
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
RUNS = P1_ROOT / "results" / "runs"
OUT = P1_ROOT / "results" / "p2_input"
BLOCK_M_TASKS = {"v1_STM01", "v1_STM02", "v1_RFS01", "v1_RFS02"}


def formal_runs() -> list[Path]:
    return sorted(RUNS.glob("v1_formal_A_rep*")) + sorted(
        RUNS.glob("v1_formal_M_*")
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows_out = []
    usage_agg = defaultdict(lambda: {
        "steps": 0, "prompt_tokens": 0, "completion_tokens": 0,
        "cached_tokens": 0, "cached_missing": 0,
        "mech_runs_pass": 0, "mech_runs_total": 0,
    })
    for run_dir in formal_runs():
        meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
        policy = meta.get("history_policy")
        block = "M" if policy == "redact" else "A"
        mech_path = run_dir / "mechanism_check.json"
        mech = json.loads(mech_path.read_text(encoding="utf-8")) if mech_path.is_file() else {}
        mech_by_task = {t["task_id"]: bool(t.get("q3a_q3b_pass")) for t in mech.get("tasks", [])}
        with (run_dir / "per_step.csv").open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                res_path = (
                    run_dir / "episodes" / row["episode"] / row["baseline"]
                    / "steps" / row["step"] / "result.json"
                )
                cached = None
                omitted_est = 0
                n_verified = 0
                if res_path.is_file():
                    res = json.loads(res_path.read_text(encoding="utf-8"))
                    raw = res.get("raw_usage") or {}
                    details = raw.get("prompt_tokens_details") or {}
                    cached = details.get("cached_tokens")
                    audit = res.get("assemble_audit") or []
                    omitted_est = sum(
                        int(a.get("omitted_tokens_est") or 0) for a in audit
                    )
                    n_verified = int(res.get("n_verified_safe_omissions") or 0)
                key = (block, row["baseline"])
                agg = usage_agg[key]
                agg["steps"] += 1
                agg["prompt_tokens"] += int(row["prompt_tokens"])
                agg["completion_tokens"] += int(row["completion_tokens"])
                if cached is None:
                    agg["cached_missing"] += 1
                else:
                    agg["cached_tokens"] += int(cached)
                rows_out.append({
                    "run_id": run_dir.name,
                    "block": block,
                    "history_policy": policy,
                    "repetition_id": int(meta.get("rep") or 0),
                    "task_id": row["episode"],
                    "baseline": row["baseline"],
                    "step": row["step"],
                    "eval_success": row["eval_success"],
                    "prompt_tokens": int(row["prompt_tokens"]),
                    "completion_tokens": int(row["completion_tokens"]),
                    "total_tokens": int(row["total_tokens"]),
                    "cached_tokens": "" if cached is None else int(cached),
                    "cached_tokens_missing": int(cached is None),
                    "history_file_blocks": int(row.get("history_file_blocks") or 0),
                    "history_code_chars": int(row.get("history_code_chars") or 0),
                    "omitted_tokens_est": omitted_est,
                    "verified_safe_omission": n_verified,
                    "model_latency_ms": float(row["t_model_ms"]),
                    "episode_latency_ms": float(row["t_step_ms"]),
                    "mechanism_triggered": int(mech_by_task.get(row["episode"], 0)),
                    "usage_source": row["usage_source"],
                    "error": row.get("error") or "",
                })
    fields = list(rows_out[0].keys())
    with (OUT / "formal_runs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows_out)
    for (block, baseline), agg in sorted(usage_agg.items()):
        pass
    summary = {
        "source_runs": [r.name for r in formal_runs()],
        "step_rows": len(rows_out),
        "blocks": sorted({r["block"] for r in rows_out}),
        "by_block_baseline": {
            f"{b}/{bl}": a for (b, bl), a in sorted(usage_agg.items())
        },
        "notes": (
            "cached_tokens 来自 raw_usage.prompt_tokens_details；服务端未返回时 "
            "cached_tokens_missing=1 且字段为空（不估算）。"
        ),
    }
    (OUT / "usage_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "data_dictionary.md").write_text(
        """# P2 输入数据字典（formal_runs.csv）

| 列 | 含义 | 来源 |
| --- | --- | --- |
| run_id | 正式 run 目录名 | 目录名 |
| block | A（keep/条件A）或 M（redact/条件M） | run_meta.history_policy |
| history_policy | keep / redact | run_meta |
| repetition_id | rep 编号（1..3） | run_meta.rep |
| task_id | v1_* 任务 ID | per_step.episode |
| baseline | 五组基线之一 | per_step.baseline |
| step | step1/step2 | per_step.step |
| eval_success | 1/0 | per_step |
| prompt/completion/total_tokens | API 真实计数 | per_step（usage=api） |
| cached_tokens | 服务端前缀缓存命中；缺失为空 | result.raw_usage.prompt_tokens_details |
| cached_tokens_missing | 1=服务端未提供 | 派生 |
| history_file_blocks / history_code_chars | 请求历史中 FILE 块数/代码字符 | per_step |
| omitted_tokens_est | 该步 assemble_audit 中估算省略 token 合计（**估算**） | result.assemble_audit |
| verified_safe_omission | 该步已验证安全省略文件数（谓词 O） | result.n_verified_safe_omissions |
| model_latency_ms | 单步模型 HTTP 墙钟 | per_step.t_model_ms |
| episode_latency_ms | 单步端到端（含 eval/写盘） | per_step.t_step_ms |
| mechanism_triggered | 该 run 内该任务必需机制事件是否全部触发 | mechanism_check.json |
| usage_source / error | 计数来源与错误 | per_step |

**纪律**：omitted_tokens_est ≠ 真实节省；cached_tokens 是服务端行为，不等于
VAM 记忆仓；REUSE_KV 是文本省略代理。
""",
        encoding="utf-8",
    )
    print(f"rows={len(rows_out)} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
