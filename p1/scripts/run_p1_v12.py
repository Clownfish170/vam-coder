#!/usr/bin/env python
"""VAM-Coder V1.2 P0 runner：消融臂 E/F/G/H（dry-run 优先）。

不覆盖 run_p1_v11.py / run_p1.py。

用法（仓库根）:
  python p1/scripts/run_p1_v12.py --episode v1_RUR02 --arm E --dry-run
  python p1/scripts/run_p1_v12.py --p0-dry-run   # 8任务 × E,F,G,H
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import inspect
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = P1_ROOT.parent
# holdout 适配（rev3 允许的最小适配）：--tasks-json 可将任务根切到
# p1/tasks_v13_holdout/；默认保持 p1/tasks/（V1.0 行为不变）。
TASKS_ROOT = P1_ROOT / "tasks"
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vam_coder.config import AppConfig  # noqa: E402
from vam_coder.invalidation import InvalidationManager  # noqa: E402
from vam_coder.logging_util import JsonlLogger  # noqa: E402
from vam_coder.store import StaticStore  # noqa: E402

from p1_common import (  # noqa: E402
    SYSTEM_PROMPT,
    apply_blocks,
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
import p1_common as _p1c  # noqa: E402

from v12.assemble import AssembledV12, assemble_v12  # noqa: E402
from v12.audit import V12Audit  # noqa: E402
from v12.config import load_arm  # noqa: E402
from v12.levels import build_plan  # noqa: E402
from v12.proof import tracker_from_history  # noqa: E402
from v12.messages_visibility import verify_omissions_in_messages  # noqa: E402
from v12.history_project import project_history  # noqa: E402
from v12.obligations import open_lines, parse_obligation, raise_sha  # noqa: E402
from v12.hist_external import bm25_select, summarize_history  # noqa: E402
from v12.targets import parse_edit_targets  # noqa: E402
from v11.visibility import VisibilityTracker, content_sha256  # noqa: E402

V12_ARMS = {
    "E": "vam_coder_v1.2_E",
    "F": "vam_coder_v1.2_F",
    "G": "vam_coder_v1.2_G",
    "H": "vam_coder_v1.2_H",
    "V13A": "vam_coder_v1.3_V13A",  # adaptive_a opt-in; does not alter E/F/G/H
    "V13B": "vam_coder_v1.3_V13B",  # F-default with no-body→NONE; does not alter E/F
    "V13ACR": "vam_coder_v1.3A_CR",  # content-addressed related non-target (MEM expand)
    "V13ASID": "vam_coder_v1.3A_SID",  # single-ID compact control arm
    "V13AICG": "vam_coder_v1.3A_ICG",  # information-coverage greedy optional FULL
    "V13BICG": "vam_coder_v1.3B_ICG",  # V13B iteration: ICG default (post-testpart)
    "V13BTESTPART": "vam_coder_v1.3B_testpart",  # ICG+C (testpart lineage)
    "V13BSP": "vam_coder_v1.3B_special",  # ICG+OSCA+retrieval+C
    "V13DVAD": "vam_coder_v1.3D_VAD",  # V13D: ICG + verified slow distill
    "V13EPROJ": "vam_coder_v1.3E_PROJ",  # V13E·SAH: F + 历史状态投影（S1 消融）
    "V13ESAH": "vam_coder_v1.3E_SAH",  # V13E·SAH: F + 投影 + 义务账本（主臂）
    "V13ICGSAH": "vam_coder_v1.3E_ICGSAH",  # V13E·SAH: ICG + 投影 + 账本（全栈）
    # V13E 外部对照臂（论文对比表）
    "TRUNC": "vam_coder_ext_TRUNC",  # 滑窗截断（预算由 args.max_history_chars 按臂覆盖）
    "SUMM": "vam_coder_ext_SUMM",  # LLM 摘要压缩（摘要器成本全计）
    "RETR": "vam_coder_ext_RETR",  # BM25 top-k 历史检索
    "MEMORYOFF": "memory_off",  # baseline: full repo dump each step (no VAM memory)
}
P0_TASKS = [
    "v1_RUR02",
    "v1_RUR03",
    "v1_DEL01",
    "v1_DUP01",
    "v1_CFD01",
    "v1_STM02",
    "v1_RFS01",
    "v1_IRR01",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def should_call_model(ctx, check) -> tuple[bool, str]:
    """M3-FIX-01：真实模型请求前门闩。

    返回 (allow, reason)。insufficient 或 verify 未通过 → 禁止调用 chat_completion。
    """
    if getattr(ctx, "insufficient", False):
        reasons = list(getattr(ctx, "insufficient_reasons", []) or [])
        detail = ";".join(reasons) if reasons else "INSUFFICIENT"
        return False, f"INSUFFICIENT: model call skipped ({detail})"
    if check is not None and not getattr(check, "ok", True):
        miss = list(getattr(check, "missing_or_mismatch", []) or [])
        return False, f"INSUFFICIENT: model call skipped (pre_send_fail:{miss})"
    return True, ""


def copy_project(project_dir: Path, workspace: Path) -> None:
    import shutil
    if workspace.exists():
        shutil.rmtree(workspace)
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
                "qualified_name": e.qualified_name,
            }
        )
    return out


def symbol_index(store: StaticStore, repo_id: str) -> dict[str, list[str]]:
    """qualified_name -> files；symbol_id short name -> files。"""
    out: dict[str, list[str]] = {}
    for e in store.list_symbols(repo_id).values():
        rel = posix(e.file_path)
        for key in (e.qualified_name, e.qualified_name.split(".")[-1] if e.qualified_name else None):
            if key:
                out.setdefault(key, [])
                if rel not in out[key]:
                    out[key].append(rel)
    return out


def workspace_snapshot(workspace: Path) -> tuple[dict[str, str], dict[str, int], dict[str, str]]:
    files, sizes, sha = {}, {}, {}
    for p in sorted(workspace.rglob("*.py")):
        rel = posix(p.relative_to(workspace))
        if rel.startswith("eval/") or "__pycache__" in rel:
            continue
        # public-repo snapshots may contain latin-1/non-utf8 .py; don't crash the episode
        text = p.read_text(encoding="utf-8", errors="replace")
        files[rel] = text
        sizes[rel] = len(text.encode("utf-8"))
        sha[rel] = content_sha256(text)
    return files, sizes, sha


def run_episode_arm(
    *,
    episode: dict,
    arm: str,
    out_dir: Path,
    model: str,
    endpoint: str,
    args,
    cfg: AppConfig,
    rep: int,
    slow_store=None,
) -> list[dict]:
    ep_id = episode["id"]
    baseline = V12_ARMS[arm]
    # rep>1 使用独立目录，避免覆盖 R1 产物
    arm_dir = baseline if rep <= 1 else f"{baseline}_R{rep}"
    base_dir = out_dir / "episodes" / ep_id / arm_dir
    workspace = base_dir / "workspace"
    steps_dir = base_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    copy_project(TASKS_ROOT / ep_id / "project", workspace)

    arm_cfg = load_arm(
        arm,
        closure_depth=args.closure_depth,
        budget_tokens=args.budget_tokens,
        context_window=args.context_window,
        # P2 消融开关（prereg §6）；默认 False → 覆盖值与冻结配置一致
        must_full_dep_closure=not getattr(args, "no_must_closure", False),
        o_prime=not getattr(args, "no_oprime", False),
        sah_project_mode=getattr(args, "sah_project_mode", "last"),
    )
    audit = V12Audit(path=base_dir / "logs" / "injection_audit.jsonl")
    # episode 级 tracker 仅作诊断；O′ 授权用每步 history 证明 + 发送前强制校验
    tracker_diag = VisibilityTracker()
    history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    store = manager = None
    cfg2 = copy.deepcopy(cfg)
    store, manager, cfg2 = open_memory(base_dir, cfg2)
    # V1.3A_CR / V13B：episode 级内容寻址库（与符号 store 分离）
    cr_store = None
    if getattr(arm_cfg, "cr_enabled", False):
        from cr.store import MemoryStore

        cr_store = MemoryStore()
    # V13D：跨集共享 slow_store 由参数传入；未传且开启时建 per-episode 空库
    if slow_store is None and getattr(arm_cfg, "slow_enabled", False):
        from cr.slowmem import SlowStore

        slow_store = SlowStore()
    # V13B 特别版：OSCA 跨步状态（episode 生命周期）
    icg_state: dict = {}
    t0 = time.perf_counter()
    manager.sync(workspace, ep_id)
    t_init = (time.perf_counter() - t0) * 1000.0

    rows: list[dict] = []
    ledger_tokens = 0
    # V13E·SAH：投影统计 + 义务账本（v2：窄口径 + 只留未结）
    sah_folded_total = 0
    sah_obligations: list = []  # list[v12.obligations.Obligation]
    for step_no, step in enumerate(episode["steps"], start=1):
        t_step0 = time.perf_counter()
        manager.sync(workspace, ep_id)
        ebf = entries_by_file_map(store, ep_id)
        sym_idx = symbol_index(store, ep_id)
        files, sizes, sha = workspace_snapshot(workspace)
        targets = parse_edit_targets(step["instruction"], sorted(files), sym_idx)

        # history token est
        trimmed, dropped, _ = trim_history(history, args.max_history_chars)
        if getattr(args, "history_policy", "keep") == "redact":
            trimmed = redact_assistant_code(trimmed)
        # V13E·S1：trim/redact 之后、hist_est / proof_tr / build_messages 之前投影，
        # 三者共用同一份投影后历史（证明与实发一致；对 O′ 等价，见 v13e_sah_design §3）
        sah_stats = {"folded_blocks": 0, "kept_blocks": 0}
        if getattr(arm_cfg, "sah_project", False):
            trimmed, sah_stats = project_history(
                trimmed, getattr(arm_cfg, "sah_project_mode", "last")
            )
            sah_folded_total += int(sah_stats.get("folded_blocks", 0))
        # V13E·S2（v2）：只渲染仍未结的义务（add=符号缺席；modify=提出后未再改）
        sah_ledger_lines: list[str] | None = None
        if getattr(arm_cfg, "sah_ledger", False) and sah_obligations:
            opened = open_lines(sah_obligations, files, sha)
            sah_ledger_lines = opened or None
        # ---- V13E 外部对照臂（SUMM/RETR 在投影之后、证明与发包之前介入）----
        aux_prompt_tokens = 0
        aux_completion_tokens = 0
        if getattr(arm_cfg, "hist_summary", False):
            trimmed, aux_prompt_tokens, aux_completion_tokens = summarize_history(
                trimmed,
                call_fn=chat_completion,
                endpoint=endpoint,
                model=model,
                recent=int(getattr(arm_cfg, "hist_summary_recent", 2)),
                timeout=args.timeout,
                seed=args.seed,
            )
        if getattr(arm_cfg, "hist_retrieve", False):
            trimmed, _n_hist_sel = bm25_select(
                trimmed,
                step["instruction"],
                k=int(getattr(arm_cfg, "hist_retrieve_k", 3)),
            )
        # hist_est 覆盖 history + 账本（账本随每步重发，属真实历史开销）
        hist_chars = len(json.dumps(trimmed, ensure_ascii=False)) + sum(
            len(x) for x in (sah_ledger_lines or [])
        )
        hist_est = hist_chars // max(1, cfg2.chars_per_token)
        # 阶段 A：O′ 候选证明 = trim 后将进入 messages 的历史（不含本步 context）
        proof_tr = tracker_from_history(trimmed)

        is_memory_off = baseline == "memory_off"
        if is_memory_off:
            # 基线：每步全仓源码，无 plan/O′/CR
            from p1_common import assemble_memory_off

            mo = assemble_memory_off(workspace)
            from types import SimpleNamespace

            ctx = AssembledV12(
                text=mo.text,
                file_blocks=mo.file_blocks,
                expand_included_bytes=mo.expand_included_bytes,
                notes=list(getattr(mo, "notes", []) or []),
            )
            plan = SimpleNamespace(
                edit_targets=set(),
                candidate_full=set(),
                must_full=set(),
                insufficient=False,
                insufficient_reasons=[],
                required_context_tokens_est=None,
                available_context_tokens=args.context_window,
                files=[],
                over_kmax=False,
                over_budget=False,
                dropped_optional_digest=[],
                dropped_optional_full=[],
                audit=lambda: {"arm": baseline, "memory_off": True},
            )
            check = SimpleNamespace(
                ok=True,
                missing_or_mismatch=[],
                edit_target_full_verified=True,
                candidate_full_verified=True,
                reasons={},
                revised=False,
                force_full=[],
                edit_target_missing=[],
                candidate_missing=[],
            )
            et_list: list[str] = []
            cf_list: list[str] = []
            force_full = set()
            pre_send_revise = False
            t_asm = 0.0
        else:
            plan = build_plan(
                arm_cfg=arm_cfg,
                instruction=step["instruction"],
                workspace_files=sorted(files),
                workspace_sha=sha,
                file_sizes=sizes,
                entries_by_file=ebf,
                targets=targets,
                system_history_tokens_est=hist_est,
                source_by_file=files,
                icg_state=icg_state,
            )
            t_route = 0.0  # included in plan build time
            t0 = time.perf_counter()
            force_full = set()
            ctx = assemble_v12(
                workspace,
                plan,
                proof_tr,
                arm_cfg,
                symbols_by_file=sym_idx,
                system_history_tokens_est=hist_est,
                force_full=force_full,
                record_context_marks=False,
                cr_store=cr_store,
                cr_instruction=step["instruction"],
                slow_store=slow_store,
            )
            messages = build_messages(
                trimmed, step["instruction"], ctx.text, ledger_lines=sah_ledger_lines
            )

            # 阶段 B：发送前强制校验最终 messages ↔ O′ 省略 + E/C 完整性
            disk_sha = {rel: content_sha256(text) for rel, text in files.items()}
            et_list = sorted(plan.edit_targets)
            cf_list = sorted(plan.candidate_full)
            check = verify_omissions_in_messages(
                messages,
                list(ctx.omitted_files),
                disk_sha,
                edit_targets=et_list,
                candidate_full=cf_list,
            )
            pre_send_revise = False
            if not check.ok:
                pre_send_revise = True
                force_full = set(check.missing_or_mismatch)
                ctx = assemble_v12(
                    workspace,
                    plan,
                    proof_tr,
                    arm_cfg,
                    symbols_by_file=sym_idx,
                    system_history_tokens_est=hist_est,
                    force_full=force_full,
                    record_context_marks=False,
                    cr_store=cr_store,
                    cr_instruction=step["instruction"],
                    slow_store=slow_store,
                )
                messages = build_messages(
                    trimmed, step["instruction"], ctx.text, ledger_lines=sah_ledger_lines
                )
                check2 = verify_omissions_in_messages(
                    messages,
                    list(ctx.omitted_files),
                    disk_sha,
                    edit_targets=et_list,
                    candidate_full=cf_list,
                )
                if not check2.ok:
                    ctx.insufficient = True
                    for rel in check2.missing_or_mismatch:
                        reason = (
                            "EDIT_TARGET_FULL_VERIFY_FAIL"
                            if rel in et_list
                            else "CANDIDATE_FULL_VERIFY_FAIL"
                            if rel in cf_list
                            else "PRE_SEND_VERIFY_FAIL"
                        )
                        tag = f"{reason}:{rel}"
                        if tag not in ctx.insufficient_reasons:
                            ctx.insufficient_reasons.append(tag)
                check = check2
            # V1.3A_CR：Memory/Reference 完整性（失败 → INSUFFICIENT，不发请求）
            if cr_store is not None and getattr(ctx, "cr_refs", None):
                from cr.validate import validate_cr
                from cr.resolver import Reference

                cr_refs = []
                for ra in ctx.cr_refs:
                    cr_refs.append(
                        Reference(
                            path=ra["path"],
                            purpose="related",
                            ref_kind="content",
                            content_id=ra["content_id"],
                            pin_sha256="",
                            range_kind="full",
                        )
                    )
                delivered = set()
                for a in ctx.audits:
                    if a.get("action") in ("EXPAND", "MEM_EXPAND", "DIGEST", "CR_RELATED_SKIPPED"):
                        delivered.add(a["file"])
                cr_check = validate_cr(
                    cr_refs,
                    cr_store,
                    required_paths=set(plan.must_full)
                    | set(plan.edit_targets)
                    | set(plan.candidate_full),
                    delivered_paths=delivered,
                )
                if not cr_check.ok:
                    ctx.insufficient = True
                    for code in cr_check.codes:
                        tag = f"CR_VALIDATE_FAIL:{code}"
                        if tag not in ctx.insufficient_reasons:
                            ctx.insufficient_reasons.append(tag)
            t_asm = (time.perf_counter() - t0) * 1000.0

        if is_memory_off:
            messages = build_messages(
                trimmed, step["instruction"], ctx.text, ledger_lines=sah_ledger_lines
            )
        # (else 分支已在内部生成 messages)

        step_out = steps_dir / step["id"]
        step_out.mkdir(parents=True, exist_ok=True)
        # 快照必须对应最终实际发送内容（阶段 B 修订后）
        (step_out / "context.txt").write_text(ctx.text, encoding="utf-8")
        write_json(step_out / "messages.json", messages)
        write_json(
            step_out / "pre_send_check.json",
            {
                "ok": check.ok,
                "missing_or_mismatch": check.missing_or_mismatch,
                "reasons": check.reasons,
                "revised": pre_send_revise,
                "force_full": sorted(force_full),
                "omitted_after": list(ctx.omitted_files),
                "edit_targets": et_list,
                "candidate_full": cf_list,
                "edit_target_full_verified": check.edit_target_full_verified,
                "candidate_full_verified": check.candidate_full_verified,
                "edit_target_missing": check.edit_target_missing or [],
                "candidate_missing": check.candidate_missing or [],
            },
        )

        error = ""
        prompt_tokens = completion_tokens = 0
        cached_tokens = 0
        usage_source = "none"
        t_model = 0.0
        response_text = ""
        applied: list = []
        rejected: list = []
        # M3-FIX-01：所有真实请求入口前统一门闩
        allow_model, block_reason = should_call_model(ctx, check)
        if args.dry_run:
            if not allow_model:
                error = block_reason
            else:
                error = "dry_run: model call and eval skipped"
        elif not allow_model:
            error = block_reason
            (step_out / "response.txt").write_text("", encoding="utf-8")
        else:
            cr = chat_completion(
                endpoint, model, messages,
                temperature=args.temperature, max_tokens=args.max_tokens,
                timeout=args.timeout, seed=args.seed,
            )
            t_model = cr.latency_ms
            prompt_tokens = cr.prompt_tokens
            completion_tokens = cr.completion_tokens
            ptd = (cr.raw_usage or {}).get("prompt_tokens_details") or {}
            try:
                cached_tokens = int(ptd.get("cached_tokens") or 0)
            except (TypeError, ValueError):
                cached_tokens = 0
            usage_source = cr.usage_source
            response_text = cr.text
            if cr.error:
                error = f"model_error: {cr.error}"
            (step_out / "response.txt").write_text(response_text, encoding="utf-8")
            history.append({"role": "assistant", "content": response_text})
            # V13E·S2：账本与 history 同生命周期（模型未被调用的步骤不入账）；
            # sha 取本步动作前快照 → modify 义务可判定「提出后是否动过该文件」
            if getattr(arm_cfg, "sah_ledger", False):
                sah_obligations.append(
                    raise_sha(
                        parse_obligation(step_no, step["instruction"]), sha
                    )
                )
            tracker_diag.mark_from_assistant(response_text)
            blocks = parse_file_blocks(response_text)
            applied, rejected = apply_blocks(workspace, blocks)
            write_json(step_out / "apply.json", {"applied": applied, "rejected": rejected})

        # 评测：INSUFFICIENT 或 dry-run 不评测（工作区可能不完整/无响应）
        t_eval = 0.0
        eval_success = None
        eval_output = ""
        if args.dry_run or not allow_model:
            if not allow_model and not args.dry_run:
                (step_out / "eval_output.txt").write_text(
                    "SKIPPED: INSUFFICIENT (no model call)", encoding="utf-8"
                )
        else:
            eval_dir = TASKS_ROOT / ep_id / step["eval"]
            t0 = time.perf_counter()
            eval_success, eval_output = run_eval(
                workspace, eval_dir, timeout=args.eval_timeout
            )
            t_eval = (time.perf_counter() - t0) * 1000.0
            (step_out / "eval_output.txt").write_text(eval_output, encoding="utf-8")

        ledger_tokens += prompt_tokens + completion_tokens + aux_prompt_tokens + aux_completion_tokens

        audit.record(
            {
                "episode": ep_id,
                "step": step["id"],
                "arm": arm,
                "baseline": baseline,
                "rep": rep,
                "config_sha256": arm_cfg.digest(),
                "config": arm_cfg.to_dict(),
                "targets": {
                    "exact_paths": sorted(targets.exact_paths),
                    "exact_symbols": sorted(targets.exact_symbols),
                    "ambiguous_symbols": sorted(targets.ambiguous_symbols),
                    "fuzzy_only_hits": sorted(targets.fuzzy_only_hits),
                },
                "plan": plan.audit(),
                "levels": [
                    {"path": f.relpath, "level": f.level, "is_must": f.is_must,
                     "r": f.r_score, "reason": f.reason}
                    for f in plan.files
                ],
                "checks": ctx.audits,
                "pre_send": {
                    "ok": check.ok,
                    "missing_or_mismatch": check.missing_or_mismatch,
                    "reasons": check.reasons,
                    "revised": pre_send_revise,
                    "force_full": sorted(force_full),
                    "edit_target_full_verified": check.edit_target_full_verified,
                    "candidate_full_verified": check.candidate_full_verified,
                },
                "post": {
                    "injected_files": [a["file"] for a in ctx.audits if a["action"] == "EXPAND"],
                    "digest_files": [a["file"] for a in ctx.audits if a["action"] == "DIGEST"],
                    "omitted_files": list(ctx.omitted_files),
                    "verified_safe_omissions": ctx.verified_safe_omissions,
                    "insufficient": ctx.insufficient,
                    "insufficient_reasons": list(ctx.insufficient_reasons),
                    "required_context_tokens_est": ctx.required_context_tokens_est,
                    "available_context_tokens": ctx.available_context_tokens,
                },
            }
        )

        t_step = (time.perf_counter() - t_step0) * 1000.0
        row = {
            "episode": ep_id,
            "step": step["id"],
            "baseline": baseline,
            "arm": arm,
            "rep": rep,
            "model": model,
            "eval_success": "" if eval_success is None else int(eval_success),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached_tokens": cached_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "usage_source": usage_source,
            "context_file_blocks": ctx.file_blocks,
            "context_digest_lines": ctx.digest_lines,
            "n_verified_safe_omissions": ctx.verified_safe_omissions,
            "insufficient": int(ctx.insufficient),
            "insufficient_reason": ";".join(ctx.insufficient_reasons),
            "must_full_count": len(plan.must_full),
            "over_kmax": int(plan.over_kmax),
            "over_budget": int(plan.over_budget),
            "fuzzy_only_hits": ";".join(sorted(targets.fuzzy_only_hits)),
            "edit_targets": ";".join(sorted(targets.exact_paths)),
            "dropped_optional_digest": ";".join(plan.dropped_optional_digest),
            "dropped_optional_full": ";".join(plan.dropped_optional_full),
            "t_model_ms": round(t_model, 2),
            "t_eval_ms": round(t_eval, 2),
            "t_step_ms": round(t_step, 2),
            "t_assemble_ms": round(t_asm, 2),
            "t_initial_sync_ms": round(t_init, 2),
            "context_chars": len(ctx.text),
            "sah_folded_blocks": int(sah_stats.get("folded_blocks", 0)),
            "sah_ledger_lines": len(sah_ledger_lines or []),
            "aux_prompt_tokens": int(aux_prompt_tokens),
            "aux_completion_tokens": int(aux_completion_tokens),
            "pre_send_revised": int(pre_send_revise),
            "force_full_n": len(force_full),
            "applied_files": ";".join(applied),
            "error": error,
            "architecture": "v1.2-r2.2",
            "config_sha256": arm_cfg.digest(),
            "required_context_tokens_est": plan.required_context_tokens_est,
            "available_context_tokens": plan.available_context_tokens,
        }
        write_json(step_out / "result.json", row)
        (step_out / "prompt.txt").write_text(messages[-1]["content"], encoding="utf-8")
        rows.append(row)

    write_json(
        base_dir / "ledger.json",
        {
            "arm": arm,
            "episode": ep_id,
            "total_tokens": ledger_tokens,
            "config_sha256": arm_cfg.digest(),
        },
    )
    # V13D：episode 全步成功 → 蒸馏慢层（验证锚：eval 全过 + 磁盘为步末状态）
    if slow_store is not None and rows:
        all_ok = all(int(r.get("eval_success") or 0) == 1 for r in rows)
        if all_ok:
            try:
                from cr.slowmem import distill_workspace

                units = distill_workspace(
                    workspace,
                    slow_store,
                    origin={"task_id": ep_id, "arm": arm, "rep": rep, "esr": 1},
                )
                for r in rows:
                    r["slow_distilled"] = len(units)
            except Exception as e:  # noqa: BLE001
                for r in rows:
                    r["slow_distill_error"] = f"{type(e).__name__}:{e}"
    return rows


def main(argv=None) -> int:
    global TASKS_ROOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="")
    ap.add_argument("--arm", default="E", choices=list(V12_ARMS))
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--model", default="qwen2.5-coder-1.5b")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--eval-timeout", type=float, default=60.0)
    ap.add_argument("--pause-seconds", type=float, default=0.0)
    ap.add_argument("--max-history-chars", type=int, default=24000)
    ap.add_argument("--closure-depth", type=int, default=2)
    ap.add_argument("--budget-tokens", type=int, default=4096)
    ap.add_argument("--context-window", type=int, default=8192)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--arms", default="", help="逗号分隔 E,F,G,H；覆盖 --arm")
    ap.add_argument("--p0-dry-run", action="store_true")
    ap.add_argument("--out-root", default="")
    ap.add_argument(
        "--history-policy", choices=("keep", "redact"), default="keep",
        help="P2 消融-5：redact = assistant 代码块脱敏（默认 keep 与冻结一致）",
    )
    ap.add_argument("--no-must-closure", action="store_true",
                    help="P2 消融-3：must_full_dep_closure=False")
    ap.add_argument("--no-oprime", action="store_true",
                    help="P2 消融-4：o_prime=False")
    ap.add_argument(
        "--tasks-json",
        default="",
        help="任务清单 JSON；给定时任务根取其所在目录（holdout 用 p1/tasks_v13_holdout/holdout_tasks.json）",
    )
    args = ap.parse_args(argv)

    tasks_path = (
        Path(args.tasks_json)
        if args.tasks_json
        else (P1_ROOT / "tasks" / "tasks_v1.0.json")
    )
    TASKS_ROOT = tasks_path.parent
    meta = json.loads(tasks_path.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in meta["episodes"]}

    if args.p0_dry_run:
        args.dry_run = True
        arms = ["E", "F", "G", "H"]
        ep_ids = list(P0_TASKS)
    elif args.arms:
        arms = [a.strip().upper() for a in args.arms.split(",") if a.strip()]
        bad = [a for a in arms if a not in V12_ARMS]
        if bad:
            print(f"unknown arms: {bad}", file=sys.stderr)
            return 2
        ep_ids = [x.strip() for x in args.episode.split(",") if x.strip()] or list(P0_TASKS)
    else:
        arms = [args.arm]
        ep_ids = [x.strip() for x in args.episode.split(",") if x.strip()] or list(P0_TASKS)

    cfg = AppConfig.load(PROJECT_ROOT / "config" / "default.json")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_root = Path(args.out_root) if args.out_root else (
        P1_ROOT / "results" / "runs" / f"v12_p0_{stamp}"
    )
    out_dir = out_root
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"refusing non-empty out dir: {out_dir}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        out_dir / "run_meta.json",
        {
            "architecture": "v1.2-r2.2",
            "created_at": now_iso(),
            "model": args.model,
            "arms": arms,
            "episodes": ep_ids,
            "rep": args.rep,
            "dry_run": args.dry_run,
            "p0_dry_run": args.p0_dry_run,
            "closure_depth_draft": args.closure_depth,
            "protocol": "p1/docs/v1.2_experiment_preregistration.md",
            "tasks_json": str(tasks_path),
            "tasks_root": str(TASKS_ROOT),
            "history_policy": getattr(args, "history_policy", "keep"),
            "ablation_flags": {
                "no_must_closure": getattr(args, "no_must_closure", False),
                "no_oprime": getattr(args, "no_oprime", False),
            },
            "frozen_hashes": {
                "system_prompt_sha256": hashlib.sha256(
                    SYSTEM_PROMPT.encode("utf-8")
                ).hexdigest(),
                "build_messages_source_sha256": hashlib.sha256(
                    inspect.getsource(_p1c.build_messages).encode("utf-8")
                ).hexdigest(),
                "p1_common_sha256": hashlib.sha256(
                    Path(_p1c.__file__).read_bytes()
                ).hexdigest(),
            },
            "config_digests": {
                a: load_arm(
                    a,
                    closure_depth=args.closure_depth,
                    budget_tokens=args.budget_tokens,
                    context_window=args.context_window,
                    must_full_dep_closure=not getattr(args, "no_must_closure", False),
                    o_prime=not getattr(args, "no_oprime", False),
                ).digest()
                for a in arms
            },
        },
    )

    all_rows: list[dict] = []
    for arm in arms:
        for eid in ep_ids:
            if eid not in by_id:
                print(f"unknown episode {eid}", file=sys.stderr)
                return 2
            print(f"[run] arm={arm} episode={eid}")
            rows = run_episode_arm(
                episode=by_id[eid],
                arm=arm,
                out_dir=out_dir,
                model=args.model,
                endpoint=args.endpoint,
                args=args,
                cfg=cfg,
                rep=args.rep,
            )
            all_rows.extend(rows)
            if args.pause_seconds and not args.dry_run:
                time.sleep(args.pause_seconds)

    fields = [
        "episode", "step", "baseline", "arm", "rep", "model", "eval_success",
        "prompt_tokens", "completion_tokens", "cached_tokens", "total_tokens", "usage_source",
        "context_file_blocks", "context_digest_lines", "n_verified_safe_omissions",
        "insufficient", "insufficient_reason", "must_full_count", "over_kmax", "over_budget",
        "fuzzy_only_hits", "edit_targets", "dropped_optional_digest", "dropped_optional_full",
        "t_model_ms", "t_step_ms", "t_assemble_ms", "t_initial_sync_ms", "context_chars",
        "applied_files", "error", "architecture", "config_sha256",
        "required_context_tokens_est", "available_context_tokens",
    ]
    with (out_dir / "per_step.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    print(f"[done] out={out_dir} rows={len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
