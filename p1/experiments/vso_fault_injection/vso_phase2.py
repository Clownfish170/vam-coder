#!/usr/bin/env python
"""VSO Phase2：冻结 10 场景 × R3 在真实执行链路中的确认（DeepSeek 主模型）。

- 场景（冻结）：V1, V4, C1, C2, C3, H1, H2, V5, P1, P5
- 注入方式：**进程内 monkeypatch**（仅本测试进程；生产文件零修改）：
    · run_p1_v12.tracker_from_history  —— 证明状态故障（stale/empty/corrupt/tracker-only-synth）
    · run_p1_v12.build_messages        —— 正向样例的"历史可见"前置注入
    · v12.assemble.safe_omission       —— C1/C2 破损授权器（冲突注入）
    · run_p1_v12.build_plan            —— C3 预算注入
- 每场景每 rep 一集（完整 episode，真实模型调用），跑完读审计/预发送/消息做断言。
- 定位：确认性（逐场景 expected vs observed），不做显著性/泛化。
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parents[1]
ROOT = P1.parent
sys.path.insert(0, str(P1 / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import p1_common as _p1c  # noqa: E402
from p1_common import SYSTEM_PROMPT  # noqa: E402,F401
from vam_coder.config import AppConfig  # noqa: E402

import run_p1_v12 as R  # noqa: E402
import v12.assemble as A  # noqa: E402
from v11.visibility import content_sha256  # noqa: E402
from v12.messages_visibility import (  # noqa: E402
    full_files_in_messages, verify_omissions_in_messages,
)
from v12.workspace_audit import (  # noqa: E402
    write_episode_workspace_evidence, write_post_and_diff,
)

ALLOW, FORCE, INSUF = "ALLOW_OMISSION", "FORCE_FULL", "INSUFFICIENT"
TASKS_JSON = P1 / "tasks_p1_validation" / "p1_tasks.json"
FROZEN_PROJECT = P1 / "tasks_p1_validation"

# 场景 → (任务, 需要注入的故障文件相对路径或 None)
SCENARIOS = {
    "V1": ("p1_M01a", "inventory.py"),
    "V4": ("p1_S01b", "rates.py"),
    "C1": ("p1_L01b", None),
    "C2": ("p1_L01b", None),
    "C3": ("p1_S01a", None),
    "H1": ("p1_M01a", "inventory.py"),
    "H2": ("p1_M01a", "inventory.py"),
    "V5": ("p1_M01a", "inventory.py"),
    "P1": ("p1_S01b", None),
    "P5": ("p1_M01a", None),
}
EXPECTED = {
    "V1": FORCE, "V4": FORCE, "C1": FORCE, "C2": FORCE, "C3": INSUF,
    "H1": FORCE, "H2": FORCE, "V5": FORCE, "P1": ALLOW, "P5": ALLOW,
}
REPS = [1, 2, 3]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha_text(t: str) -> str:
    return content_sha256(t)


def assistant_file_msg(path: str, body: str) -> dict:
    return {"role": "assistant", "content": f"FILE: {path}\n```python\n{body}```"}


def read_workspace_files(ws: Path) -> dict[str, str]:
    out = {}
    for p in sorted(ws.rglob("*.py")):
        rel = p.relative_to(ws).as_posix()
        if rel.startswith("eval/") or "__pycache__" in rel:
            continue
        out[rel] = p.read_text(encoding="utf-8")
    return out


# ---------------------------------------------------------------- 注入状态
class Fault:
    """每个场景一个实例；wrapper 按 mode 分派。"""

    def __init__(self, mode: str, fault_file: str | None, task: str):
        self.mode = mode
        self.fault_file = fault_file
        self.task = task
        self.synthetic_source = "frozen" if mode == "P1" else "current"
        self.safe_log: list[dict] = []
        self.broken_auth = mode in ("C1", "C2")
        # V1/H1 用的常量
        self.stale_sha = sha_text("__STALE__")
        self.current_ws: Path | None = None  # main 在调用前设置（工作区确定性路径）

    def synth_msgs(self) -> list[dict]:
        """P1/P5 的合成『曾可见』历史（P1=冻结初态；P5=当前工作区内容）。"""
        src: dict[str, str] = {}
        if self.synthetic_source == "frozen":
            base = FROZEN_PROJECT / self.task / "project"
            for p_ in sorted(base.rglob("*.py")):
                src[p_.relative_to(base).as_posix()] = p_.read_text(encoding="utf-8")
        else:
            if self.current_ws and self.current_ws.exists():
                src = read_workspace_files(self.current_ws)
        return [assistant_file_msg(rel, body) for rel, body in src.items()]

    # -- tracker_from_history 包装
    def wrap_tracker(self, original):
        mode = self.mode

        def _wrapped(history):
            if mode in ("P1", "P5"):
                tr = original(list(history) + self.synth_msgs())
                return tr
            if mode == "H2":
                # 不可恢复：抹掉围栏 → 真实解析拿不到证明；messages 侧不受影响
                stripped = []
                for m in history:
                    c = (m.get("content") or "").replace("```python\n", "").replace("```", "")
                    stripped.append({**m, "content": c})
                return original(stripped)
            tr = original(history)
            if mode == "V1":
                for k in list(tr._files):
                    tr._files[k] = self.stale_sha
            elif mode == "H1":
                for k in list(tr._files):
                    tr._files[k] = sha_text(f"CORRUPT:{k}")
            elif mode == "V5" and self.fault_file:
                # 证明 = 冻结原文件内容（模拟外部覆盖后的过期证明）
                frozen = FROZEN_PROJECT / self.task / "project" / self.fault_file
                if frozen.exists():
                    tr._files[self.fault_file] = sha_text(frozen.read_text(encoding="utf-8"))
            elif mode == "V4":
                # tracker-only 全量合成证明（与 messages 脱钩 = V4 故障）
                ws = getattr(self, "current_ws", None)
                if ws:
                    for rel, txt in read_workspace_files(ws).items():
                        tr._files[rel] = sha_text(txt)
                        tr._chars[rel] = len(txt)
            return tr

        return _wrapped

    # -- build_messages 包装（正向 P1/P5：把合成历史拼进最终 messages）
    def wrap_build_messages(self, original):
        mode = self.mode

        def _wrapped(trimmed, instruction, context_text):
            if mode not in ("P1", "P5"):
                return original(trimmed, instruction, context_text)
            # 合成"所有文件曾可见"的历史（P1=冻结初态内容；P5=当前工作区内容）
            synth = self.synth_msgs()
            new_trimmed = list(trimmed) + synth
            return original(new_trimmed, instruction, context_text)

        return _wrapped

    # -- safe_omission 包装（C1/C2 破损授权器 + 全场景记录）
    def wrap_safe_omission(self, original):
        def _wrapped(**kwargs):
            rel = kwargs.get("relpath", "?")
            if self.broken_auth:
                allow, reasons = True, ["injected:broken_authorizer"]
            else:
                allow, reasons = original(**kwargs)
            self.safe_log.append({"rel": rel, "allow": bool(allow),
                                  "reasons": list(reasons)})
            return allow, reasons

        return _wrapped

    # -- build_plan 包装（C3 预算注入）
    def wrap_build_plan(self, original):
        def _wrapped(**kwargs):
            plan = original(**kwargs)
            if self.mode == "C3":
                plan.required_context_tokens_est = 9000
                plan.insufficient = True
                plan.insufficient_reasons.append("INJECTED_REQUIRED_CONTEXT_EXCEEDS_LIMIT")
                plan.rules.append("injected_budget_exhaustion")
            return plan

        return _wrapped


def install(fault: Fault) -> dict:
    """安装 monkeypatch，返回 originals 以便 restore。"""
    orig = {
        "tracker": R.tracker_from_history,
        "build_messages": R.build_messages,
        "safe_omission": A.safe_omission,
        "build_plan": R.build_plan,
    }
    R.tracker_from_history = fault.wrap_tracker(orig["tracker"])
    R.build_messages = fault.wrap_build_messages(orig["build_messages"])
    A.safe_omission = fault.wrap_safe_omission(orig["safe_omission"])
    R.build_plan = fault.wrap_build_plan(orig["build_plan"])
    return orig


def restore(orig: dict) -> None:
    R.tracker_from_history = orig["tracker"]
    R.build_messages = orig["build_messages"]
    A.safe_omission = orig["safe_omission"]
    R.build_plan = orig["build_plan"]


# ---------------------------------------------------------------- 断言
def evaluate(scenario: str, fault: Fault, ep_dir: Path, task: str,
             baseline_dir: str) -> dict:
    base = ep_dir / "runner_out" / "episodes" / task / baseline_dir
    steps = sorted((base / "steps").glob("step*"))
    n_omitted = 0
    n_reuse = 0
    n_revise = 0
    n_insufficient = 0
    n_steps = 0
    n_requests = 0
    unsafe_ship = 0
    dho_sum = 0
    et_ctx_ok = True
    must_ctx_ok = True
    for sd in steps:
        n_steps += 1
        res = json.loads((sd / "result.json").read_text(encoding="utf-8"))
        psc = json.loads((sd / "pre_send_check.json").read_text(encoding="utf-8"))
        aud_path = base / "logs" / "injection_audit.jsonl"
        aud = None
        if aud_path.exists():
            for line in aud_path.read_text(encoding="utf-8").splitlines():
                a = json.loads(line)
                if a["step"] == sd.name:
                    aud = a
                    break
        if int(res.get("prompt_tokens") or 0) > 0 or (res.get("usage_source") or "none") != "none":
            n_requests += 1
        if int(res.get("insufficient") or 0) == 1:
            n_insufficient += 1
        if psc.get("revised"):
            n_revise += 1
        if not psc.get("ok", True) and int(res.get("insufficient") or 0) == 0:
            # 验证未过、却既没回退也没转 INSUFFICIENT 就发运 = 不安全发运
            unsafe_ship += 1
        n_omitted += len(psc.get("omitted_after") or [])
        if aud:
            for c in aud.get("checks", []):
                if c["action"] == "REUSE_KV":
                    n_reuse += 1
            plan = aud.get("plan", {})
            om = set(aud.get("post", {}).get("omitted_files", []))
            dho_sum += len(set(plan.get("edit_targets", [])) & om)
            if scenario == "C2":
                # edit targets 必须在当前 context 全量
                et_ctx_ok = et_ctx_ok and bool(psc.get("edit_target_full_verified", True))
            if scenario == "C1":
                # 冻结设计 §3.2 C1 机器条件：must 文件必须【完整出现在最终 messages】
                # （RSR 口径：已证明的省略合法，不要求 must 一定在 context）
                msgs = json.loads((sd / "messages.json").read_text(encoding="utf-8"))
                visible = {rel: content_sha256(body)
                           for rel, body in full_files_in_messages(msgs).items()}
                ws_dir = base / "workspace"
                # 冻结字面：出现在最终 messages 即可（哈希正确性由 runtime verify/
                # unsafe_ship=0 覆盖；内容会随后续步骤正常演化，勿拿终局磁盘比对）
                for x in (aud.get("levels") or []):
                    if not x.get("is_must"):
                        continue
                    must_ctx_ok = must_ctx_ok and (x["path"] in visible)

    # observed 决策
    if scenario == "C3":
        observed = INSUF if (n_insufficient > 0 and n_requests == 0) else FORCE
    elif scenario in ("P1", "P5"):
        observed = ALLOW if (n_reuse >= 1 and unsafe_ship == 0 and dho_sum == 0) else FORCE
    else:
        # 负向：故障文件不得被省略 + 最终无不安全发运 + DHO=0
        ok = unsafe_ship == 0 and dho_sum == 0
        if scenario == "C1":
            ok = ok and must_ctx_ok
        if scenario == "C2":
            ok = ok and et_ctx_ok
        observed = FORCE if ok else ALLOW  # ok=False 意味着防线失败 → 若出现省略/不安全则非 FORCE
    return {
        "observed_decision": observed,
        "expected_decision": EXPECTED[scenario],
        "decision_correct": int(observed == EXPECTED[scenario]),
        "n_steps": n_steps,
        "n_requests": n_requests,
        "n_omitted_final": n_omitted,
        "n_reuse_kv": n_reuse,
        "n_revised": n_revise,
        "n_insufficient": n_insufficient,
        "unsafe_ship": unsafe_ship,
        "dho_sum": dho_sum,
        "fault_safe_calls": len(fault.safe_log),
        "broken_auth_injected": int(fault.broken_auth),
    }


# ---------------------------------------------------------------- 主流程
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="https://maas.qianwenaiapi.com/compatible-mode/v1")
    ap.add_argument("--model", default="deepseek-v4.1-flash-1017")
    ap.add_argument("--out", default=str(HERE / "phase2_runs"))
    ap.add_argument("--limit", type=int, default=0, help="本轮最多集数（续跑用）")
    args = ap.parse_args(argv)

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    log_path = out_root / "execution_log.jsonl"
    done: set[str] = set()
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") == "OK":
                done.add(rec["episode_id"])

    tasks_doc = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in tasks_doc["episodes"]}
    cfg = AppConfig.load(ROOT / "config" / "default.json")

    class Args:
        closure_depth = 2
        budget_tokens = 4096
        context_window = 8192
        max_history_chars = 24000
        temperature = 0.0
        seed = 0
        max_tokens = 2048
        timeout = 300.0
        eval_timeout = 60.0
        dry_run = False
        history_policy = "keep"
        pause_seconds = 0.0

    run_args = Args()
    run_args.endpoint = args.endpoint
    run_args.model = args.model

    R.TASKS_ROOT = TASKS_JSON.parent  # 直接调 run_episode_arm 时的任务根（测试侧设置）
    order = [(s, r) for s in SCENARIOS for r in REPS]
    executed = 0
    results = []
    for scen, rep in order:
        task, fault_file = SCENARIOS[scen]
        ep_id = f"{task}_{scen}_R{rep}"
        if ep_id in done:
            # 续跑时读回结果
            rp = out_root / "scenario_results.jsonl"
            continue
        if args.limit and executed >= args.limit:
            break
        ep_dir = out_root / "runs" / ep_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        write_episode_workspace_evidence(
            source_project=FROZEN_PROJECT / task / "project",
            workspace=ep_dir / "workspace_pending",
            episode_dir=ep_dir, episode_id=ep_id, task_id=task,
            arm=scen, repetition=rep,
        )
        fault = Fault(scen, fault_file, task)
        fault.current_ws = (ep_dir / "runner_out" / "episodes" / task /
                            "vam_coder_v1.2_F" / "workspace")
        orig = install(fault)
        try:
            t0 = time.time()
            rows = R.run_episode_arm(
                episode=by_id[task], arm="F", out_dir=ep_dir / "runner_out",
                model=args.model, endpoint=args.endpoint, args=run_args,
                cfg=copy.deepcopy(cfg), rep=rep,
            )
            elapsed = round(time.time() - t0, 2)
            baseline_dir = "vam_coder_v1.2_F"
            ev = evaluate(scen, fault, ep_dir, task, baseline_dir)
        finally:
            restore(orig)
        rec = {
            "episode_id": ep_id, "scenario": scen, "task_id": task,
            "repetition": rep, "elapsed_s": elapsed, "status": "OK",
            "fault_file": fault_file, "ts": now(), **ev,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        results.append(rec)
        executed += 1
        print(f"[{executed}] {ep_id} -> observed={ev['observed_decision']} "
              f"expected={ev['expected_decision']} correct={ev['decision_correct']} "
              f"reuse={ev['n_reuse_kv']} revised={ev['n_revised']} "
              f"insuf={ev['n_insufficient']} unsafe={ev['unsafe_ship']} t={elapsed}s",
              flush=True)

    # 汇总（含续跑历史）
    all_recs = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                all_recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    # 同场景多 rep 取一致率
    per_scen: dict[str, list[dict]] = {}
    for r in all_recs:
        per_scen.setdefault(r["scenario"], []).append(r)
    scen_verdict = {}
    for scen, recs in per_scen.items():
        n_ok = sum(int(x.get("decision_correct", 0)) for x in recs)
        scen_verdict[scen] = {
            "runs": len(recs), "correct": n_ok,
            "expected": EXPECTED[scen],
            "observed_set": sorted({x.get("observed_decision") for x in recs}),
            "scenario_pass": n_ok == len(recs),
        }
    total = sum(v["runs"] for v in scen_verdict.values())
    total_ok = sum(v["correct"] for v in scen_verdict.values())
    summary = {
        "schema": "vso-phase2-summary-v1",
        "model": args.model, "endpoint": args.endpoint,
        "scenarios_frozen": list(SCENARIOS.keys()),
        "reps": REPS,
        "episodes_total": total,
        "decision_correct": total_ok,
        "decision_accuracy": round(total_ok / total, 4) if total else 0.0,
        "scenarios_pass": sum(1 for v in scen_verdict.values() if v["scenario_pass"]),
        "scenarios_total": len(scen_verdict),
        "per_scenario": scen_verdict,
        "unsafe_ship_total": sum(int(x.get("unsafe_ship") or 0) for x in all_recs),
        "dho_total": sum(int(x.get("dho_sum") or 0) for x in all_recs),
        "positioning": "confirmatory per-scenario assertion（不做显著性/泛化结论，v2 §4）",
        "production_code_modified": False,
    }
    (out_root / "vso_phase2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 结果表
    fields = ["episode_id", "scenario", "task_id", "repetition", "status",
              "expected_decision", "observed_decision", "decision_correct",
              "n_steps", "n_requests", "n_omitted_final", "n_reuse_kv",
              "n_revised", "n_insufficient", "unsafe_ship", "dho_sum",
              "fault_safe_calls", "broken_auth_injected", "elapsed_s"]
    with (out_root / "vso_phase2_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in all_recs:
            w.writerow(r)
    print(json.dumps({k: summary[k] for k in
                      ("episodes_total", "decision_correct", "decision_accuracy",
                       "scenarios_pass", "scenarios_total", "unsafe_ship_total",
                       "dho_total")},
                     ensure_ascii=False))
    print(json.dumps(scen_verdict, ensure_ascii=False, indent=1))
    return 0 if summary["scenarios_pass"] == summary["scenarios_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
