#!/usr/bin/env python
"""VAM-Coder V1.1 实验入口：新增 baseline `vam_coder_v1.1`。

与冻结的 run_p1.py 并行存在；不修改 P0/v1.0 行为。

用法（仓库根）：
    python p1/scripts/run_p1_v11.py --episode v1_RUR02 --baselines vam_coder_v1.1 --dry-run
    python p1/scripts/run_p1_v11.py --episode v1_RUR02,v1_DEL01 \\
        --baselines memory_off,vam_coder_v1.1 --rep 1 --pause-seconds 2
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

P1_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = P1_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vam_coder.config import AppConfig  # noqa: E402
from vam_coder.invalidation import InvalidationManager  # noqa: E402
from vam_coder.logging_util import JsonlLogger  # noqa: E402
from vam_coder.store import StaticStore  # noqa: E402

from p1_common import (  # noqa: E402
    SYSTEM_PROMPT,
    apply_blocks,
    assemble_memory_off,
    assemble_symbol_full_read,
    build_messages,
    chat_completion,
    history_code_metrics,
    parse_file_blocks,
    posix,
    redact_assistant_code,
    run_eval,
    tokens_estimate_chars,
    trim_history,
    write_json,
)

from v11.assemble import assemble_vam_v11  # noqa: E402
from v11.audit import CostLedger, InjectionAudit  # noqa: E402
from v11.controller import MemoryController, RetrievePlan  # noqa: E402
from v11.visibility import VisibilityTracker, content_sha256  # noqa: E402

V11_BASELINE = "vam_coder_v1.1"
BASELINES = (
    "memory_off",
    "symbol_full_read",
    "fixed_summary",
    "vam_coder",
    "refreshed_summary",
    V11_BASELINE,
)
MEMORY_BASELINES = (
    "symbol_full_read",
    "fixed_summary",
    "vam_coder",
    "refreshed_summary",
    V11_BASELINE,
)

CSV_FIELDS = [
    "episode", "step", "baseline", "rep", "baseline_order_index", "model",
    "eval_success",
    "prompt_tokens", "completion_tokens", "total_tokens", "usage_source",
    "context_tokens_est", "history_tokens_est", "n_messages", "router_est_tokens",
    "t_initial_sync_ms", "t_sync_ms", "t_route_ms", "t_assemble_ms",
    "t_model_ms", "t_eval_ms", "t_step_ms",
    "n_expand", "n_reuse_kv", "n_compress", "n_drop",
    "n_stale", "n_unverified", "n_tombstoned",
    "reuse_decisions", "reuse_omitted", "reuse_omitted_files",
    "reuse_omitted_bytes", "reuse_without_omission", "expand_included_bytes",
    "n_verified_safe_omissions", "history_file_blocks", "history_code_chars",
    "context_file_blocks", "context_summary_blocks",
    "context_chars", "response_chars",
    "applied_files", "rejected_files", "history_pairs_dropped", "error",
    "architecture", "emc_need", "emc_mode", "fallback_events",
    "insufficient_context", "ledger_total_tokens",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def copy_project(project_dir: Path, workspace: Path) -> None:
    if workspace.exists():
        import shutil
        shutil.rmtree(workspace)
    import shutil
    shutil.copytree(project_dir, workspace)


def open_memory(base_dir: Path, cfg: AppConfig):
    db = base_dir / "store.db"
    dec = base_dir / "logs" / "decisions.jsonl"
    inv = base_dir / "logs" / "invalidation_events.jsonl"
    for p in (db, dec, inv):
        if p.exists():
            p.unlink()
    cfg.db_path = str(db)
    cfg.decision_log = str(dec)
    cfg.invalidation_log = str(inv)
    store = StaticStore(db)
    manager = InvalidationManager(store, cfg, JsonlLogger(inv))
    return store, manager, cfg


def entries_by_file_map(store: StaticStore, repo_id: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for sid, e in store.list_symbols(repo_id).items():
        rel = posix(e.file_path)
        out.setdefault(rel, []).append(
            {
                "symbol_id": sid,
                "validity": e.validity,
                "source_hash": e.source_hash,
                "content_hash": e.content_hash,
                "version": e.version,
                "deps": list(e.deps or []),
                "kind": e.kind,
            }
        )
    return out


def dependency_closure_files(store: StaticStore, ep_id: str) -> set[str]:
    """从被失效/依赖边相关的符号出发收集文件，不把全库文件都算进闭包。"""
    symbols = store.list_symbols(ep_id)
    by_id = symbols
    files: set[str] = set()
    seeds: list = []
    for e in symbols.values():
        if e.validity in ("stale", "unverified", "tombstoned"):
            seeds.append(e)
    # 依赖边：若 A.deps 含 B，且 B 失效，则 A 也相关
    id_to_file = {sid: posix(e.file_path) for sid, e in symbols.items()}
    dep_ids: set[str] = set()
    for e in symbols.values():
        for dep in e.deps or []:
            if dep in by_id and by_id[dep].validity != "valid":
                dep_ids.add(dep)
                seeds.append(by_id[dep])
    for e in seeds:
        if e.validity == "tombstoned":
            continue
        files.add(posix(e.file_path))
    # 依赖了失效符号的调用方文件
    for e in symbols.values():
        if e.validity == "tombstoned":
            continue
        for dep in e.deps or []:
            if dep in by_id and by_id[dep].validity != "valid":
                files.add(posix(e.file_path))
    return files


def workspace_file_list(workspace: Path) -> list[str]:
    from p1_common import _read_workspace_files
    return sorted(_read_workspace_files(workspace))


def build_v11_plan(
    *,
    instruction: str,
    workspace: Path,
    store: StaticStore,
    ep_id: str,
    tracker: VisibilityTracker,
    controller: MemoryController,
) -> tuple[RetrievePlan, float, dict[str, str]]:
    t0 = time.perf_counter()
    ws_files = {
        posix(p.relative_to(workspace)): p.read_text(encoding="utf-8")
        for p in sorted(workspace.rglob("*.py"))
        if not str(posix(p.relative_to(workspace))).startswith("eval/")
    }
    sha_map = {k: content_sha256(v) for k, v in ws_files.items()}
    ebf = entries_by_file_map(store, ep_id)
    closure = dependency_closure_files(store, ep_id)
    plan = controller.decide(
        instruction=instruction,
        workspace_files=sorted(ws_files),
        entries_by_file=ebf,
        visibility_paths=set(tracker.visible_paths()),
        dependency_closure_files=closure,
        workspace_sha=sha_map,
    )
    plan = controller.apply_visibility_veto(plan, tracker, sha_map)
    # 缺失文件强制 insufficient 标记在装配层
    ms = (time.perf_counter() - t0) * 1000.0
    return plan, ms, sha_map


def run_episode_baseline(
    *,
    episode: dict,
    baseline: str,
    out_dir: Path,
    model: str,
    endpoint: str,
    args,
    cfg: AppConfig,
    rep: int,
    order_index: int,
) -> tuple[list[dict], dict]:
    ep_id = episode["id"]
    base_dir = out_dir / "episodes" / ep_id / baseline
    workspace = base_dir / "workspace"
    steps_dir = base_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    copy_project(P1_ROOT / "tasks" / ep_id / "project", workspace)

    store = manager = None
    history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    t_initial_sync_ms = 0.0
    tracker = VisibilityTracker()
    ledger = CostLedger()
    audit = InjectionAudit(path=base_dir / "logs" / "injection_audit.jsonl")
    controller = MemoryController()
    is_v11 = baseline == V11_BASELINE

    if baseline in MEMORY_BASELINES:
        cfg = copy.deepcopy(cfg)
        store, manager, cfg = open_memory(base_dir, cfg)
        t0 = time.perf_counter()
        manager.sync(workspace, ep_id)
        t_initial_sync_ms = (time.perf_counter() - t0) * 1000.0

    step_rows: list[dict] = []
    try:
        for idx, step in enumerate(episode["steps"], start=1):
            t_step0 = time.perf_counter()
            t_sync = t_route = t_assemble = 0.0
            error = ""
            counts_val = {"stale": 0, "unverified": 0, "tombstoned": 0, "valid": 0}
            counts_dec = {"EXPAND": 0, "REUSE_KV": 0, "COMPRESS": 0, "DROP": 0}
            router_est = 0
            emc_need = ""
            emc_mode = ""
            fallback_events = 0
            insufficient = False
            n_verified = 0
            n_omitted_files = 0
            n_omitted_bytes = 0
            n_expand_bytes = 0
            file_blocks = 0

            if baseline in MEMORY_BASELINES:
                t0 = time.perf_counter()
                manager.sync(workspace, ep_id)
                t_sync = (time.perf_counter() - t0) * 1000.0
                for e in store.list_symbols(ep_id).values():
                    counts_val[e.validity] = counts_val.get(e.validity, 0) + 1

            t0 = time.perf_counter()
            if baseline == "memory_off":
                ctx = assemble_memory_off(workspace)
                file_blocks = ctx.file_blocks
                n_expand_bytes = ctx.expand_included_bytes
            elif baseline == "symbol_full_read":
                files = sorted(
                    {
                        posix(e.file_path)
                        for e in store.list_symbols(ep_id).values()
                        if e.validity != "tombstoned"
                    }
                )
                ctx = assemble_symbol_full_read(workspace, files)
                file_blocks = ctx.file_blocks
                n_expand_bytes = ctx.expand_included_bytes
            elif is_v11:
                plan, t_route, _sha = build_v11_plan(
                    instruction=step["instruction"],
                    workspace=workspace,
                    store=store,
                    ep_id=ep_id,
                    tracker=tracker,
                    controller=controller,
                )
                router_est = plan.estimated_inject_tokens
                emc_need = "1" if plan.need else "0"
                emc_mode = plan.mode
                ctx = assemble_vam_v11(
                    workspace,
                    plan.files,
                    tracker,
                    mode_banner=getattr(args, "mode_banner", "short"),
                    chars_per_token=cfg.chars_per_token,
                )
                file_blocks = ctx.file_blocks
                n_verified = ctx.n_verified_safe_omissions
                n_omitted_files = ctx.reuse_omitted_files
                n_omitted_bytes = ctx.reuse_omitted_bytes
                n_expand_bytes = ctx.expand_included_bytes
                fallback_events = ctx.fallback_events
                insufficient = ctx.insufficient
                for p in plan.files:
                    counts_dec[p.action] = counts_dec.get(p.action, 0) + 1
                audit.record(
                    {
                        "episode": ep_id,
                        "step": step["id"],
                        "baseline": baseline,
                        "rep": rep,
                        "plan": {
                            "need": plan.need,
                            "mode": plan.mode,
                            "rules": plan.rules_fired,
                            "files": [
                                {
                                    "path": p.relpath,
                                    "action": p.action,
                                    "reason": p.reason,
                                    "validity": p.validity,
                                }
                                for p in plan.files
                            ],
                        },
                        "checks": ctx.audits,
                        "post": {
                            "injected_files": [
                                a["file"] for a in ctx.audits if a["action"] == "EXPAND"
                            ],
                            "omitted_files": list(ctx.omitted_files),
                            "verified_safe_omissions": n_verified,
                            "fallback_events": fallback_events,
                            "insufficient": insufficient,
                        },
                        "visible_paths": tracker.visible_paths(),
                    }
                )
            else:
                # 其余基线：不支持（本入口仅 memory_off / symbol / v1.1）
                ctx = assemble_memory_off(workspace)
                error = f"baseline_not_supported_in_v11_runner:{baseline}"
            t_assemble = (time.perf_counter() - t0) * 1000.0 - t_route

            step_out = steps_dir / step["id"]
            step_out.mkdir(parents=True, exist_ok=True)
            (step_out / "context.txt").write_text(ctx.text, encoding="utf-8")

            trimmed, dropped_pairs, history_chars = trim_history(
                history, args.max_history_chars
            )
            if args.history_policy == "redact":
                trimmed = redact_assistant_code(trimmed)
            messages = build_messages(trimmed, step["instruction"], ctx.text)
            hmetrics = history_code_metrics(messages)
            (step_out / "prompt.txt").write_text(messages[-1]["content"], encoding="utf-8")
            write_json(step_out / "messages.json", messages)
            messages_sha = hashlib.sha256(
                json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            context_tokens_est = tokens_estimate_chars(ctx.text, cfg.chars_per_token)
            history_tokens_est = tokens_estimate_chars(
                json.dumps(trimmed, ensure_ascii=False), cfg.chars_per_token
            )

            prompt_tokens = completion_tokens = 0
            usage_source = "none"
            t_model = 0.0
            response_text = ""
            raw_usage: dict = {}
            http_status = None
            response_model = None
            req_started = req_ended = None
            applied: list = []
            rejected: list = []
            params = {
                "temperature": args.temperature,
                "seed": args.seed,
                "max_tokens": args.max_tokens,
                "stream": False,
            }
            if args.dry_run:
                error = "dry_run: model call and eval skipped"
            else:
                cr = chat_completion(
                    endpoint,
                    model,
                    messages,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    timeout=args.timeout,
                    seed=args.seed,
                )
                t_model = cr.latency_ms
                prompt_tokens = cr.prompt_tokens
                completion_tokens = cr.completion_tokens
                usage_source = cr.usage_source
                response_text = cr.text
                raw_usage = cr.raw_usage or {}
                http_status = cr.http_status
                response_model = cr.response_model
                req_started = cr.started_at
                req_ended = cr.ended_at
                if cr.error:
                    error = f"model_error: {cr.error}"
                (step_out / "response.txt").write_text(response_text, encoding="utf-8")
                history.append({"role": "assistant", "content": response_text})
                if is_v11:
                    tracker.mark_from_assistant(response_text)
                blocks = parse_file_blocks(response_text)
                applied, rejected = apply_blocks(workspace, blocks)
                write_json(
                    step_out / "apply.json",
                    {"applied": applied, "rejected": rejected},
                )

            write_json(
                step_out / "request.json",
                {
                    "model_requested": model,
                    "response_model": response_model,
                    "endpoint": endpoint,
                    "params": params,
                    "started_at": req_started,
                    "ended_at": req_ended,
                    "http_status": http_status,
                    "latency_ms": round(t_model, 2),
                    "messages_path": "messages.json",
                    "messages_sha256": messages_sha,
                    "n_messages": len(messages),
                    "history_tokens_est": history_tokens_est,
                    "context_tokens_est": context_tokens_est,
                    "usage_raw": raw_usage if raw_usage else None,
                    "usage_source": usage_source,
                    "error": error or None,
                },
            )

            t_eval = 0.0
            eval_success = None
            eval_output = ""
            if not args.dry_run:
                eval_dir = P1_ROOT / "tasks" / ep_id / step["eval"]
                t0 = time.perf_counter()
                eval_success, eval_output = run_eval(
                    workspace, eval_dir, timeout=args.eval_timeout
                )
                t_eval = (time.perf_counter() - t0) * 1000.0
                (step_out / "eval_output.txt").write_text(eval_output, encoding="utf-8")

            t_step = (time.perf_counter() - t_step0) * 1000.0
            ledger.add_step(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                index_ms=t_sync,
                route_ms=t_route,
                assemble_ms=max(0.0, t_assemble),
                fallback_events=fallback_events,
                injected_chars=n_expand_bytes,
                omitted_chars_est=n_omitted_bytes,
                verified_safe_omission_files=n_verified,
                model_latency_ms=t_model,
            )

            row = {
                "episode": ep_id,
                "step": step["id"],
                "baseline": baseline,
                "rep": rep,
                "baseline_order_index": order_index,
                "model": model,
                "eval_success": "" if eval_success is None else int(eval_success),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "usage_source": usage_source,
                "context_tokens_est": context_tokens_est,
                "history_tokens_est": history_tokens_est,
                "n_messages": len(messages),
                "router_est_tokens": router_est,
                "t_initial_sync_ms": round(t_initial_sync_ms, 2),
                "t_sync_ms": round(t_sync, 2),
                "t_route_ms": round(t_route, 2),
                "t_assemble_ms": round(t_assemble, 2),
                "t_model_ms": round(t_model, 2),
                "t_eval_ms": round(t_eval, 2),
                "t_step_ms": round(t_step, 2),
                "n_expand": counts_dec.get("EXPAND", 0),
                "n_reuse_kv": counts_dec.get("REUSE_KV", 0),
                "n_compress": counts_dec.get("COMPRESS", 0),
                "n_drop": counts_dec.get("DROP", 0),
                "n_stale": counts_val.get("stale", 0),
                "n_unverified": counts_val.get("unverified", 0),
                "n_tombstoned": counts_val.get("tombstoned", 0),
                "reuse_decisions": counts_dec.get("REUSE_KV", 0),
                "reuse_omitted": n_omitted_files,
                "reuse_omitted_files": n_omitted_files,
                "reuse_omitted_bytes": n_omitted_bytes,
                "reuse_without_omission": 0,
                "expand_included_bytes": n_expand_bytes,
                "n_verified_safe_omissions": n_verified,
                "history_file_blocks": hmetrics["history_file_blocks"],
                "history_code_chars": hmetrics["history_code_chars"],
                "context_file_blocks": file_blocks,
                "context_summary_blocks": getattr(ctx, "summary_blocks", 0),
                "context_chars": len(ctx.text),
                "response_chars": len(response_text or ""),
                "applied_files": ";".join(applied),
                "rejected_files": ";".join(rejected),
                "history_pairs_dropped": dropped_pairs,
                "error": error,
                "architecture": "v1.1" if is_v11 else "v1.0-harness",
                "emc_need": emc_need,
                "emc_mode": emc_mode,
                "fallback_events": fallback_events,
                "insufficient_context": int(insufficient),
                "ledger_total_tokens": ledger.tokens_total,
            }
            write_json(
                step_out / "result.json",
                {
                    **row,
                    "assemble_audit": getattr(ctx, "assemble_audit", ctx.audits if is_v11 else []),
                    "v11_ledger": ledger.to_dict(),
                    "v11_plan_rules": plan.rules_fired if is_v11 else [],
                },
            )
            step_rows.append(row)
            if args.pause_seconds and not args.dry_run:
                time.sleep(args.pause_seconds)

        summary = {
            "episode": ep_id,
            "baseline": baseline,
            "rep": rep,
            "steps": len(step_rows),
            "eval_successes": sum(
                1 for r in step_rows if str(r.get("eval_success")) == "1"
            ),
            "errors": sum(1 for r in step_rows if r.get("error")),
            "verified_safe_omissions_total": sum(
                int(r.get("n_verified_safe_omissions") or 0) for r in step_rows
            ),
            "ledger": ledger.to_dict(),
        }
        write_json(base_dir / "ledger.json", ledger.to_dict())
        return step_rows, summary
    finally:
        pass


def rotation_order(baselines: list[str], ep_idx: int, rep: int):
    off = (ep_idx + rep) % len(baselines)
    return baselines[off:] + baselines[:off], off


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="VAM-Coder V1.1 runner")
    ap.add_argument("--episode", default="all")
    ap.add_argument("--baselines", default=V11_BASELINE)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--model", default="qwen2.5-coder-1.5b")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--eval-timeout", type=float, default=60.0)
    ap.add_argument("--pause-seconds", type=float, default=2.0)
    ap.add_argument("--max-history-chars", type=int, default=24000)
    ap.add_argument("--history-policy", choices=("keep", "redact"), default="keep")
    ap.add_argument("--budget-tokens", type=int, default=4096)
    ap.add_argument("--mode-banner", choices=("none", "short", "long"), default="short")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-root", default=None)
    args = ap.parse_args(argv)

    tasks_dir = P1_ROOT / "tasks"
    task_ids = sorted(
        p.name for p in tasks_dir.iterdir() if p.is_dir() and p.name.startswith("v1_")
    )
    if args.episode != "all":
        wanted = [e.strip() for e in args.episode.split(",") if e.strip()]
        missing = [w for w in wanted if w not in task_ids]
        if missing:
            print(f"unknown episodes: {missing}", file=sys.stderr)
            return 2
        ep_ids = wanted
    else:
        ep_ids = task_ids

    baselines = [b.strip() for b in args.baselines.split(",") if b.strip()]
    bad = [b for b in baselines if b not in BASELINES]
    if bad:
        print(f"unknown baselines: {bad}", file=sys.stderr)
        return 2

    tasks_meta = json.loads((tasks_dir / "tasks_v1.0.json").read_text(encoding="utf-8"))
    episodes_meta = tasks_meta.get("episodes") or []
    by_id = {t["id"]: t for t in episodes_meta}
    episodes = []
    for eid in ep_ids:
        if eid not in by_id:
            print(f"missing task metadata: {eid}", file=sys.stderr)
            return 2
        episodes.append(by_id[eid])

    cfg = AppConfig.load(PROJECT_ROOT / "config" / "default.json")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_root = Path(args.out_root) if args.out_root else (
        P1_ROOT / "results" / "runs" / f"v11_{stamp}_{args.model}"
    )
    out_dir = out_root
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"refusing non-empty out dir: {out_dir}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    run_meta = {
        "architecture_runner": "p1/scripts/run_p1_v11.py",
        "created_at": now_iso(),
        "model": args.model,
        "endpoint": args.endpoint,
        "baselines": baselines,
        "episodes": ep_ids,
        "rep": args.rep,
        "history_policy": args.history_policy,
        "mode_banner": args.mode_banner,
        "dry_run": args.dry_run,
        "task_set_mode": (
            "validation_subset"
            if args.episode != "all" and len(ep_ids) <= 12
            else "full_or_custom"
        ),
        "branch": "p1/v1.1",
        "protocol": "p1/docs/v1.1/v1.1_experiment_protocol.md",
    }
    write_json(out_dir / "run_meta.json", run_meta)

    all_rows: list[dict] = []
    summaries: list[dict] = []
    for ei, ep in enumerate(episodes):
        order, off = rotation_order(baselines, ei, args.rep)
        print(f"[episode] {ep['id']} order={order}")
        for oi, baseline in enumerate(order):
            print(f"[run] {ep['id']} {baseline} ...")
            rows, summary = run_episode_baseline(
                episode=ep,
                baseline=baseline,
                out_dir=out_dir,
                model=args.model,
                endpoint=args.endpoint,
                args=args,
                cfg=cfg,
                rep=args.rep,
                order_index=oi,
            )
            all_rows.extend(rows)
            summaries.append(summary)

    with (out_dir / "per_step.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    write_json(out_dir / "summary.json", summaries)
    print(f"[done] out={out_dir} steps={len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
