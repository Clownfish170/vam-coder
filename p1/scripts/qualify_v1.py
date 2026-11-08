#!/usr/bin/env python
"""P1-v1.0 资格报告生成器：Q1→Q2→Q3a→Q3b→Q4→Q5→Q6，检查器先于分类。

用法：
    python p1/scripts/qualify_v1.py \
        --run p1/results/runs/<qual_run_id> \
        --selfcheck p1/results/selfcheck_v1_report.json \
        --predecl p1/tasks/predeclared_mechanisms_v1.0.json
输出：<run>/qualification_report.{json,md}；退出码 0（生成成功，含 FAIL 标签也返回 0——标签供人工/流程处理）。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_mechanisms_v1 import check_run, sha256_file  # noqa: E402

DIFFICULTY = {
    "v1_CFD01": "E", "v1_CFD02": "M", "v1_CFD03": "M",
    "v1_SIG01": "E", "v1_SIG02": "M", "v1_SIG03": "H",
    "v1_REN01": "E", "v1_REN02": "M",
    "v1_DEL01": "E", "v1_DEL02": "M",
    "v1_DUP01": "M", "v1_DUP02": "H",
    "v1_IRR01": "E", "v1_IRR02": "M",
    "v1_CLS01": "M", "v1_CLS02": "H",
    "v1_STM01": "M", "v1_STM02": "M", "v1_STM03": "H",
    "v1_RFS01": "M", "v1_RFS02": "M",
    "v1_RUR01": "M", "v1_RUR02": "E", "v1_RUR03": "E",
}
INFRA_ERRORS = ("MODEL_HTTP_ERROR", "HARNESS_ERROR", "EVAL_TIMEOUT")
BASELINES = ("memory_off", "symbol_full_read", "fixed_summary",
             "vam_coder", "refreshed_summary")


def load_rows(run_dir: Path) -> list[dict]:
    with (run_dir / "per_step.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def classify_error(row: dict) -> str:
    err = row.get("error") or ""
    if "dry_run" in err:
        return "DRY_RUN"
    if "HTTPError" in err or "URLError" in err or "model_error" in err:
        return "MODEL_HTTP_ERROR"
    if "EVAL_TIMEOUT" in (row.get("eval_output_placeholder") or ""):
        return "EVAL_TIMEOUT"
    if row.get("eval_success") == "0":
        if row.get("rejected_files") and not row.get("applied_files"):
            return "APPLY_REJECTED"
        if row.get("response_chars", "0") in ("0", ""):
            return "MODEL_NO_EDIT"
        return "EVAL_FAIL"
    if row.get("eval_success") == "1":
        return "PASS"
    return "OTHER"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--selfcheck", required=True)
    ap.add_argument("--predecl", required=True)
    args = ap.parse_args()
    run_dir = Path(args.run)
    rows = load_rows(run_dir)
    selfcheck = json.loads(Path(args.selfcheck).read_text(encoding="utf-8"))
    mechs = check_run(run_dir, Path(args.predecl), None)
    mech_by_task = {t["task_id"]: t for t in mechs["tasks"]}

    # 按 (episode, baseline) 聚合 step 行
    per: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        per.setdefault((r["episode"], r["baseline"]), []).append(r)

    task_ids = sorted({r["episode"] for r in rows})
    labels = []
    for tid in task_ids:
        sc_ok = all(
            x["passed"] for x in selfcheck["results"] if x["task"] == tid
        )
        mech = mech_by_task.get(tid, {})
        entries = mech.get("entries", [])
        req_inv = [e for e in entries
                   if e["required"] and e["kind"] == "invalidation"]
        req_om = [e for e in entries
                  if e["required"] and e["kind"] == "omission"]
        q3a_fail = any(not e["result"].get("matched") for e in req_inv)
        q3b_fail = any(not e["result"].get("matched") for e in req_om)

        # Q2: ≥4 baselines 同 step 基础设施错误
        infra = False
        for step in ("step1", "step2"):
            bad = 0
            for b in BASELINES:
                rs = [r for r in per.get((tid, b), []) if r["step"] == step]
                if rs and classify_error(rs[0]) in INFRA_ERRORS:
                    bad += 1
            if bad >= 4:
                infra = True

        step_rows = {b: {r["step"]: r for r in per.get((tid, b), [])}
                     for b in BASELINES}
        all_step1_fail = all(
            step_rows.get(b, {}).get("step1", {}).get("eval_success") == "0"
            for b in BASELINES
        )
        all_pass = all(
            step_rows.get(b, {}).get(s, {}).get("eval_success") == "1"
            for b in BASELINES for s in ("step1", "step2")
        )
        all_no_edit_step1 = all(
            classify_error(step_rows.get(b, {}).get("step1", {}))
            in ("MODEL_NO_EDIT", "APPLY_REJECTED")
            for b in BASELINES
        )
        vam_rows = [r for r in per.get((tid, "vam_coder"), [])]
        vam_omit_total = sum(
            int(r.get("n_verified_safe_omissions") or 0) for r in vam_rows
        )

        # Q 规则顺序
        if not sc_ok:
            label, reason = "EXCLUDE-设计", "Q1: selfcheck 未全过"
        elif infra:
            label, reason = "EXCLUDE-设施", "Q2: ≥4 基线同步基础设施错误"
        elif q3a_fail:
            missing = [
                e["target"] for e in req_inv
                if not e["result"].get("matched")
            ]
            label, reason = (
                "REVIEW",
                f"Q3a: 必需事件缺失 {missing}（三分诊断：模型违例/实现缺陷/规格不可达）",
            )
        elif q3b_fail:
            label, reason = (
                "REVIEW",
                "Q3b: 已验证安全省略未达 min_count（三分诊断，不得因全过判 TRIVIAL）",
            )
        elif all_no_edit_step1 and DIFFICULTY.get(tid) == "E":
            label, reason = "REVIEW", "Q4: E 难度 step1 五组全部 NO_EDIT/REJECTED"
        elif all_step1_fail:
            label, reason = "CAP", "Q5: 五组 step1 全部失败（模型能力上限分层）"
        elif all_pass and (
            (req_om and not q3b_fail)
            or (not req_om and vam_omit_total == 0)
        ):
            label, reason = "TRIVIAL", "Q6: 全过且无省略区分度（保留作地板/对照）"
        else:
            label, reason = "OK", "通过全部适用 Q 规则"
        labels.append({
            "task_id": tid, "label": label, "reason": reason,
            "difficulty": DIFFICULTY.get(tid, "?"),
            "q3a_required": len(req_inv), "q3b_required": len(req_om),
            "mechanism_pass": mech.get("q3a_q3b_pass"),
        })

    report = {
        "run": str(run_dir),
        "predeclared_sha256": sha256_file(Path(args.predecl)),
        "mechanism_all_required_passed": mechs["all_required_passed"],
        "labels": labels,
    }
    (run_dir / "qualification_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# P1-v1.0 资格报告",
        f"- run: `{run_dir}`",
        f"- 预声明表 sha256: `{report['predeclared_sha256']}`",
        f"- 机制必需事件总通过: {mechs['all_required_passed']}",
        "",
        "| task | difficulty | label | reason |",
        "| --- | --- | --- | --- |",
    ]
    for x in labels:
        lines.append(
            f"| {x['task_id']} | {x['difficulty']} | **{x['label']}** | {x['reason']} |"
        )
    (run_dir / "qualification_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    from collections import Counter
    counts = Counter(x["label"] for x in labels)
    print(dict(counts))
    print(f"report -> {run_dir / 'qualification_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
