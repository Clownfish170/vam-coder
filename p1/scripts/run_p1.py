#!/usr/bin/env python
"""P1 统一实验入口（P1-v0.2）：多基线在同一任务集/模型/判定下运行并全量留痕。

用法（仓库根目录）：
    python p1/scripts/run_p1.py --episode inventory_dependency --dry-run
    python p1/scripts/run_p1.py --episode all --baselines all --rep 1 \
        --endpoint http://127.0.0.1:8080/v1 --model qwen2.5-coder-1.5b

输出（p1/results/runs/<时间戳>_<model>_rep<N>/，目录已存在且非空则拒绝）：
    run_meta.json   哈希锚点、git、服务/模型元数据、基线顺序、历史策略
    per_step.csv    逐步骤指标（计时分列；复用量三口径；token 三分）
    summary.csv     episode × baseline 聚合
    episodes/<ep>/<baseline>/…（workspace / store / logs / steps）

每步产物：context.txt、prompt.txt、messages.json、request.json
（params/时间戳/HTTP 状态/raw usage）、response.txt、apply.json、
eval_output.txt、result.json。

退出码：0 成功；2 参数/环境错误；3 清单校验失败（评测/脚本与冻结清单不一致）。
注意：REUSE_KV 是文本上下文省略代理，不是真实 KV Cache 复用。
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.metadata as md
import json
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

P1_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = P1_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vam_coder.config import AppConfig  # noqa: E402
from vam_coder.invalidation import InvalidationManager  # noqa: E402
from vam_coder.logging_util import JsonlLogger  # noqa: E402
from vam_coder.pipeline import route_repo  # noqa: E402
from vam_coder.store import StaticStore  # noqa: E402

from p1_common import (  # noqa: E402
    SYSTEM_PROMPT,
    apply_blocks,
    assemble_fixed_summary,
    assemble_memory_off,
    assemble_refreshed_summary,
    assemble_symbol_full_read,
    assemble_vam_coder,
    build_messages,
    chat_completion,
    parse_file_blocks,
    posix,
    run_eval,
    tokens_estimate_chars,
    trim_history,
    write_json,
)

# 四主基线 + 一个对照（任务 6：区分“无源码”与“摘要过期”）
MAIN_BASELINES = ("memory_off", "symbol_full_read", "fixed_summary", "vam_coder")
CONTROL_BASELINES = ("refreshed_summary",)
BASELINES = MAIN_BASELINES + CONTROL_BASELINES
MEMORY_BASELINES = ("symbol_full_read", "fixed_summary", "vam_coder",
                    "refreshed_summary")

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
    "context_file_blocks", "context_summary_blocks",
    "context_chars", "response_chars",
    "applied_files", "rejected_files", "history_pairs_dropped", "error",
]

CAPABILITY_NOTES = {
    "kv_cache_reuse": "simulated_proxy",
    "kv_proxy_detail": (
        "REUSE_KV 是文本上下文省略代理：仅当符号当前内容哈希与对话中已发送"
        "内容一致时省略。不是真实 KV 张量复用，不主张任何 KV 加速或显存收益。"
        "服务端若返回 cached_tokens 等字段，原样保存在 raw_usage，单独解释。"
    ),
    "summary_generation": "P0 docstring stub（非模型生成）",
    "model_inference": "implemented via OpenAI-compatible /chat/completions",
    "expand_source_read": "implemented by harness（P0 只输出决策）",
    "token_estimates": "context_tokens_est/history_tokens_est 为 chars/4 估算；router est_tokens 为 P0 估算；prompt_tokens 为 API 真实计数",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dir_sha256(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists():
        return "missing"
    for p in sorted(path.rglob("*")):
        if p.is_file():
            h.update(posix(p.relative_to(path)).encode("utf-8"))
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


def file_manifest(directory: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not directory.exists():
        return out
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            out[posix(p.relative_to(directory))] = sha256_file(p)
    return out


def git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip()
    except OSError:
        return ""


def probe_server(endpoint: str, timeout: float = 3.0) -> dict:
    """尽力探测 /version、/v1/models、/props；失败记 None，不伪造。"""
    base = endpoint.rstrip("/")
    root = base[:-3] if base.endswith("/v1") else base
    out: dict = {
        "version": None, "served_models": None, "props": None, "error": [],
    }
    for key, url in (
        ("version", root + "/version"),
        ("models", base + "/models"),
        ("props", root + "/props"),
    ):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                body = json.loads(r.read().decode("utf-8"))
            if key == "models":
                out["served_models"] = [m.get("id") for m in body.get("data", [])]
            else:
                out[key] = body
        except Exception as exc:  # noqa: BLE001 — 尽力探测
            out["error"].append(f"{key}: {type(exc).__name__}")
    return out


_MODEL_HASH_CACHE = P1_ROOT / ".cache" / "model_file_hashes.json"


def model_file_sha256(gguf_path: str) -> dict:
    """GGUF 文件 sha256（带本地缓存：路径+大小+mtime 为键）。"""
    p = Path(gguf_path)
    if not p.is_file():
        return {"path": gguf_path, "sha256": None, "note": "file not found"}
    stat = p.stat()
    key = str(p.resolve())
    cache: dict = {}
    if _MODEL_HASH_CACHE.is_file():
        try:
            cache = json.loads(_MODEL_HASH_CACHE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cache = {}
    rec = cache.get(key)
    if (
        rec
        and rec.get("size") == stat.st_size
        and rec.get("mtime") == stat.st_mtime
    ):
        return {"path": key, "sha256": rec["sha256"], "note": "cached"}
    digest = sha256_file(p)
    cache[key] = {
        "sha256": digest, "size": stat.st_size, "mtime": stat.st_mtime,
    }
    _MODEL_HASH_CACHE.parent.mkdir(parents=True, exist_ok=True)
    _MODEL_HASH_CACHE.write_text(
        json.dumps(cache, indent=2), encoding="utf-8"
    )
    return {"path": key, "sha256": digest, "note": "computed"}


def quant_tag(model_name: str, served_ids: list[str] | None) -> str:
    for cand in [model_name, *(served_ids or [])]:
        m = re.search(r"[-_](q\d_[a-z0-9]+)", cand or "", re.I)
        if m:
            return m.group(1).lower()
    return "unknown"


def dep_versions() -> dict:
    out = {}
    for name in ("tree-sitter", "tree-sitter-python", "blake3", "pytest"):
        try:
            out[name] = md.version(name)
        except md.PackageNotFoundError:
            out[name] = "unknown"
    return out


def hardware_info() -> dict:
    info = {
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "gpu": "unknown",
    }
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            info["gpu"] = out.stdout.strip().splitlines()[0].strip()
    except OSError:
        pass
    return info


def rotation_order(
    baselines: list[str], ep_idx: int, rep: int
) -> tuple[list[str], int]:
    """可复现轮换：偏移 = (episode 索引 + rep) % N；返回 (顺序, 偏移)。"""
    off = (ep_idx + rep) % len(baselines)
    return baselines[off:] + baselines[:off], off


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def copy_project(project_dir: Path, workspace: Path) -> None:
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


def symbol_files(store: StaticStore, repo_id: str) -> list[str]:
    return sorted(
        {
            posix(e.file_path)
            for e in store.list_symbols(repo_id).values()
            if e.validity != "tombstoned"
        }
    )


def summary_map(store: StaticStore, repo_id: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for sid, e in store.list_symbols(repo_id).items():
        if e.validity == "tombstoned":
            continue
        out[sid] = {
            "qualified_name": e.qualified_name,
            "summary": e.summary or "",
            "validity": e.validity,
            "file_path": posix(e.file_path),
        }
    return out


def validity_counts(store: StaticStore, repo_id: str) -> dict[str, int]:
    counts = {"stale": 0, "unverified": 0, "tombstoned": 0, "valid": 0}
    for e in store.list_symbols(repo_id).values():
        counts[e.validity] = counts.get(e.validity, 0) + 1
    return counts


def decision_counts(decisions: list[dict]) -> dict[str, int]:
    counts = {"EXPAND": 0, "REUSE_KV": 0, "COMPRESS": 0, "DROP": 0}
    for d in decisions:
        counts[d["action"]] = counts.get(d["action"], 0) + 1
    return counts


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

    store = None
    manager = None
    frozen: dict[str, dict] = {}
    history_sent: dict[str, str] = {}
    history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    t_initial_sync_ms = 0.0

    if baseline in MEMORY_BASELINES:
        cfg = copy.deepcopy(cfg)
        store, manager, cfg = open_memory(base_dir, cfg)
        # episode 级初始 sync：建索引/冻结记忆；单列 t_initial_sync_ms，
        # 不计入任何 t_step_ms（任务 4：只计一次，不重复）
        t0 = time.perf_counter()
        manager.sync(workspace, ep_id)
        t_initial_sync_ms = (time.perf_counter() - t0) * 1000.0
        if baseline == "fixed_summary":
            frozen = summary_map(store, ep_id)

    step_rows: list[dict] = []
    try:
        for idx, step in enumerate(episode["steps"], start=1):
            t_step0 = time.perf_counter()
            t_sync = 0.0
            t_route = 0.0
            t_assemble = 0.0
            decisions: list[dict] = []
            counts_dec = {"EXPAND": 0, "REUSE_KV": 0, "COMPRESS": 0, "DROP": 0}
            counts_val = {"stale": 0, "unverified": 0, "tombstoned": 0}
            router_est = 0
            error = ""

            # ---- 步内同步（记忆类基线；fixed_summary 不再 sync）----
            if baseline in ("symbol_full_read", "vam_coder", "refreshed_summary"):
                t0 = time.perf_counter()
                manager.sync(workspace, ep_id)
                t_sync = (time.perf_counter() - t0) * 1000.0
                vc = validity_counts(store, ep_id)
                counts_val = {k: vc.get(k, 0) for k in counts_val}

            # ---- 路由（仅 vam_coder）----
            if baseline == "vam_coder":
                t0 = time.perf_counter()
                result = route_repo(
                    store, ep_id, cfg,
                    budget_tokens=args.budget_tokens,
                    episode_id=ep_id,
                    step_id=step["id"],
                    task_content=step["instruction"],
                    logger=JsonlLogger(base_dir / "logs" / "decisions.jsonl"),
                )
                t_route = (time.perf_counter() - t0) * 1000.0
                decisions = [d.to_dict() for d in result.decisions]
                counts_dec = decision_counts(decisions)
                router_est = result.total_estimated_tokens

            # ---- 装配上下文 ----
            t0 = time.perf_counter()
            if baseline == "memory_off":
                ctx = assemble_memory_off(workspace)
            elif baseline == "symbol_full_read":
                ctx = assemble_symbol_full_read(workspace, symbol_files(store, ep_id))
            elif baseline == "fixed_summary":
                extra = ""
                if not frozen:
                    extra = (
                        "NOTE: memory is empty for symbols created after "
                        "episode start."
                    )
                ctx = assemble_fixed_summary(frozen, extra_note=extra)
            elif baseline == "refreshed_summary":
                ctx = assemble_refreshed_summary(summary_map(store, ep_id))
            else:
                entries = store.list_symbols(ep_id)
                ctx = assemble_vam_coder(
                    workspace, decisions, entries, history_sent,
                    chars_per_token=cfg.chars_per_token,
                )
            t_assemble = (time.perf_counter() - t0) * 1000.0

            step_out = steps_dir / step["id"]
            step_out.mkdir(parents=True, exist_ok=True)
            (step_out / "context.txt").write_text(ctx.text, encoding="utf-8")

            # ---- 统一历史策略（四基线同一函数/预算/截断规则）----
            trimmed, dropped_pairs, history_chars = trim_history(
                history, args.max_history_chars
            )
            messages = build_messages(trimmed, step["instruction"], ctx.text)
            (step_out / "prompt.txt").write_text(
                messages[-1]["content"], encoding="utf-8"
            )
            (step_out / "messages.json").write_text(
                json.dumps(messages, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            messages_sha = hashlib.sha256(
                json.dumps(messages, ensure_ascii=False, sort_keys=True).encode(
                    "utf-8"
                )
            ).hexdigest()
            context_tokens_est = tokens_estimate_chars(
                ctx.text, cfg.chars_per_token
            )
            history_tokens_est = tokens_estimate_chars(
                json.dumps(trimmed, ensure_ascii=False), cfg.chars_per_token
            )

            # ---- 模型调用 ----
            prompt_tokens = 0
            completion_tokens = 0
            usage_source = "none"
            t_model = 0.0
            response_text = ""
            raw_usage: dict = {}
            http_status = None
            response_model = None
            req_started = None
            req_ended = None
            applied: list[str] = []
            rejected: list[dict] = []
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
                    endpoint, model, messages,
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
                (step_out / "response.txt").write_text(
                    response_text, encoding="utf-8"
                )
                history.append({"role": "assistant", "content": response_text})
                blocks = parse_file_blocks(response_text)
                applied, rejected = apply_blocks(workspace, blocks)
                (step_out / "apply.json").write_text(
                    json.dumps(
                        {"applied": applied, "rejected": rejected},
                        ensure_ascii=False, indent=2,
                    ),
                    encoding="utf-8",
                )

            # 请求级审计副本（不含任何鉴权头；usage 缺失字段保持缺失）
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
                    "usage_note": (
                        "raw server usage object; fields not provided by the "
                        "server are absent (not fabricated)"
                    ),
                    "error": error or None,
                    "auth_headers_logged": False,
                },
            )

            # ---- 评测（与模型工作区隔离）----
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
                (step_out / "eval_output.txt").write_text(
                    eval_output, encoding="utf-8"
                )

            t_step = (time.perf_counter() - t_step0) * 1000.0
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
                "t_initial_sync_ms": (
                    round(t_initial_sync_ms, 2) if idx == 1 else 0.0
                ),
                "t_sync_ms": round(t_sync, 2),
                "t_route_ms": round(t_route, 2),
                "t_assemble_ms": round(t_assemble, 2),
                "t_model_ms": round(t_model, 2),
                "t_eval_ms": round(t_eval, 2),
                "t_step_ms": round(t_step, 2),
                "n_expand": counts_dec["EXPAND"],
                "n_reuse_kv": counts_dec["REUSE_KV"],
                "n_compress": counts_dec["COMPRESS"],
                "n_drop": counts_dec["DROP"],
                "n_stale": counts_val["stale"],
                "n_unverified": counts_val["unverified"],
                "n_tombstoned": counts_val["tombstoned"],
                "reuse_decisions": ctx.reuse_decisions,
                "reuse_omitted": ctx.reuse_omitted,
                "reuse_omitted_files": ctx.reuse_omitted_files,
                "reuse_omitted_bytes": ctx.reuse_omitted_bytes,
                "reuse_without_omission": ctx.reuse_without_omission,
                "expand_included_bytes": ctx.expand_included_bytes,
                "context_file_blocks": ctx.file_blocks,
                "context_summary_blocks": ctx.summary_blocks,
                "context_chars": len(ctx.text),
                "response_chars": len(response_text),
                "applied_files": ";".join(applied),
                "rejected_files": ";".join(r["path"] for r in rejected),
                "history_pairs_dropped": dropped_pairs,
                "error": error,
            }
            step_rows.append(row)
            write_json(
                step_out / "result.json",
                {
                    **row,
                    "decisions": decisions,
                    "raw_usage": raw_usage,
                    "assemble_notes": ctx.notes,
                    "history_policy": {
                        "max_history_chars": args.max_history_chars,
                        "history_chars_after_trim": history_chars,
                        "pairs_dropped": dropped_pairs,
                        "rule": "drop oldest user+assistant pairs; never "
                                "truncate system or the current turn",
                    },
                },
            )
    finally:
        if store is not None:
            store.close()

    successes = [r["eval_success"] for r in step_rows if r["eval_success"] != ""]
    sum_steps = sum(r["t_step_ms"] for r in step_rows)
    ep_summary = {
        "episode": ep_id,
        "baseline": baseline,
        "rep": rep,
        "baseline_order_index": order_index,
        "model": model,
        "steps": len(step_rows),
        "steps_evaluated": len(successes),
        "steps_passed": sum(1 for s in successes if s),
        "t_initial_sync_ms": round(t_initial_sync_ms, 2),
        "t_episode_ms": round(t_initial_sync_ms + sum_steps, 2),
        "t_steps_sum_ms": round(sum_steps, 2),
        "mean_total_tokens": _mean([r["total_tokens"] for r in step_rows]),
        "mean_prompt_tokens": _mean([r["prompt_tokens"] for r in step_rows]),
        "mean_model_ms": _mean([r["t_model_ms"] for r in step_rows]),
        "mean_system_ms": _mean(
            [r["t_sync_ms"] + r["t_route_ms"] + r["t_assemble_ms"] for r in step_rows]
        ),
        "mean_step_ms": _mean([r["t_step_ms"] for r in step_rows]),
        "reuse_omitted_total": sum(r["reuse_omitted"] for r in step_rows),
        "reuse_decisions_total": sum(r["reuse_decisions"] for r in step_rows),
        "reuse_omitted_bytes_total": sum(
            r["reuse_omitted_bytes"] for r in step_rows
        ),
        "history_pairs_dropped_total": sum(
            r["history_pairs_dropped"] for r in step_rows
        ),
        "errors": [r["error"] for r in step_rows if r["error"]],
    }
    write_json(base_dir / "episode_summary.json", ep_summary)
    return step_rows, ep_summary


def _mean(xs: list[float]) -> float:
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else 0.0


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def collect_hashes(tasks_path: Path, tasks: dict) -> dict:
    """运行时哈希集合（与清单同构，供校验）。"""
    eval_hashes = {}
    project_hashes = {}
    for ep in tasks["episodes"]:
        project_hashes[ep["id"]] = dir_sha256(P1_ROOT / "tasks" / ep["id"] / "project")
        for step in ep["steps"]:
            key = f"{ep['id']}/{step['id']}"
            eval_hashes[key] = dir_sha256(P1_ROOT / "tasks" / ep["id"] / step["eval"])
    return {
        "tasks_sha256": sha256_file(tasks_path),
        "script_sha256": {
            "run_p1.py": sha256_file(Path(__file__)),
            "p1_common.py": sha256_file(
                Path(__file__).resolve().parent / "p1_common.py"
            ),
        },
        "eval_dir_sha256": eval_hashes,
        "project_dir_sha256": project_hashes,
    }


def check_manifest(manifest_path: Path, live: dict) -> list[str]:
    """返回不一致列表；空列表 = 通过。清单字段缺失记为 mismatch。"""
    mismatches: list[str] = []
    try:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"manifest unreadable: {exc}"]
    for key in ("tasks_sha256",):
        if man.get(key) != live.get(key):
            mismatches.append(
                f"{key}: manifest={man.get(key)} live={live.get(key)}"
            )
    for name, digest in live["script_sha256"].items():
        m = man.get("script_sha256", {}).get(name)
        if m != digest:
            mismatches.append(f"script {name}: manifest={m} live={digest}")
    for key, digest in live["eval_dir_sha256"].items():
        m = man.get("eval_dir_sha256", {}).get(key)
        if m != digest:
            mismatches.append(f"eval {key}: manifest={m} live={digest}")
    for key, digest in live["project_dir_sha256"].items():
        m = man.get("project_dir_sha256", {}).get(key)
        if m != digest:
            mismatches.append(f"project {key}: manifest={m} live={digest}")
    return mismatches


def default_manifest() -> Path | None:
    mdir = P1_ROOT / "manifests"
    if not mdir.is_dir():
        return None
    cands = sorted(mdir.glob("p1_*_manifest*.json"))
    return cands[-1] if cands else None


def main() -> int:
    ap = argparse.ArgumentParser(description="VAM-Coder P1 实验入口（v0.2）")
    ap.add_argument("--project-root", default=str(PROJECT_ROOT))
    ap.add_argument("--tasks", default=str(P1_ROOT / "tasks" / "tasks.json"))
    ap.add_argument("--episode", default="all")
    ap.add_argument("--baselines", default="all",
                    help="逗号分隔或 all（含对照 refreshed_summary）")
    ap.add_argument("--rep", type=int, default=1,
                    help="重复编号；参与基线顺序轮换")
    ap.add_argument("--model", default="qwen2.5-coder-1.5b")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--eval-timeout", type=float, default=180.0)
    ap.add_argument("--budget-tokens", type=int, default=4096)
    ap.add_argument("--max-history-chars", type=int, default=24000,
                    help="统一历史预算（字符，四基线一致）")
    ap.add_argument("--out", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--manifest", default="",
                    help="冻结清单路径；默认取 p1/manifests/ 下最新")
    ap.add_argument("--allow-manifest-mismatch", action="store_true",
                    help="清单不一致时仅警告（用于开发；正式运行禁止）")
    ap.add_argument("--no-hash-model-file", action="store_true",
                    help="跳过 GGUF sha256（大文件耗时）")
    ap.add_argument("--server-args", default="",
                    help="推理服务启动参数原文（无法探测时人工提供）")
    ap.add_argument("--server-ctx", type=int, default=0,
                    help="推理服务上下文长度（无法探测时人工提供；0=未知）")
    args = ap.parse_args()

    tasks_path = Path(args.tasks)
    if not tasks_path.is_file():
        print(f"tasks.json not found: {tasks_path}", file=sys.stderr)
        return 2
    tasks = load_tasks(tasks_path)
    episodes = tasks["episodes"]
    if args.episode != "all":
        episodes = [e for e in episodes if e["id"] == args.episode]
        if not episodes:
            print(f"unknown episode: {args.episode}", file=sys.stderr)
            return 2
    if args.baselines == "all":
        baselines = list(BASELINES)
    else:
        baselines = [b.strip() for b in args.baselines.split(",") if b.strip()]
        bad = [b for b in baselines if b not in BASELINES]
        if bad:
            print(f"unknown baselines: {bad}", file=sys.stderr)
            return 2

    # 哈希锚点 + 清单校验（任务 1：禁止静默替换判据）
    live_hashes = collect_hashes(tasks_path, tasks)
    manifest_path = (
        Path(args.manifest) if args.manifest else (default_manifest() or Path())
    )
    manifest_check: dict = {
        "path": str(manifest_path) if args.manifest or manifest_path.name else None,
        "matched": None,
        "mismatches": [],
    }
    if manifest_path and manifest_path.is_file():
        mismatches = check_manifest(manifest_path, live_hashes)
        manifest_check["mismatches"] = mismatches
        manifest_check["matched"] = not mismatches
        if mismatches:
            print("MANIFEST MISMATCH (评测/脚本与冻结清单不一致):", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            if not args.allow_manifest_mismatch:
                print(
                    "拒绝运行：判据/脚本变更必须生成新清单与新版本，"
                    "禁止静默替换（使用 --allow-manifest-mismatch 仅限开发）。",
                    file=sys.stderr,
                )
                return 3
    else:
        manifest_check["note"] = "no manifest found; hashes still recorded"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_tag = args.model.replace("/", "_").replace(":", "_")[:40]
    out_dir = (
        Path(args.out) if args.out
        else P1_ROOT / "results" / "runs" / f"{stamp}_{model_tag}_rep{args.rep}"
    )
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"refusing to write into non-empty run dir: {out_dir}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = AppConfig.load(PROJECT_ROOT / "config" / "default.json")
    cfg.simulate_kv = True

    probe = probe_server(args.endpoint)
    served = probe.get("served_models") or []
    gguf_path = ""
    for cand in served:
        if isinstance(cand, str) and cand.lower().endswith(".gguf"):
            gguf_path = cand
            break
    model_meta = {
        "model_requested": args.model,
        "served_models": served,
        "gguf_path": gguf_path or None,
        "gguf_sha256": (
            None if args.no_hash_model_file or not gguf_path
            else model_file_sha256(gguf_path)
        ),
        "quantization_tag": quant_tag(args.model, served),
        "server_args": args.server_args or "unknown",
        "server_ctx": args.server_ctx or "unknown",
        "parallel_slots": "unknown",
    }
    props = probe.get("props") or {}
    if isinstance(props, dict):
        gen = props.get("default_generation_settings") or {}
        if not args.server_ctx and gen.get("n_ctx"):
            model_meta["server_ctx"] = gen["n_ctx"]
        if gen.get("n_parallel"):
            model_meta["parallel_slots"] = gen["n_parallel"]

    write_json(out_dir / "run_meta.json", {
        "run_id": out_dir.name,
        "p1_version": "v0.2",
        "started_at": now_iso(),
        "task_set_version": tasks.get("task_set_version"),
        "frozen_at": tasks.get("frozen_at"),
        **live_hashes,
        "manifest_check": manifest_check,
        "git_rev": git("rev-parse", "HEAD"),
        "git_branch": git("rev-parse", "--abbrev-ref", "HEAD") or "unknown",
        "git_dirty": bool(git("status", "--porcelain")),
        "p1_untracked_in_git": "?? p1/" in git("status", "--porcelain"),
        "model": model_meta,
        "endpoint": args.endpoint,
        "server_probe": probe,
        "dry_run": args.dry_run,
        "temperature": args.temperature,
        "seed": args.seed,
        "max_tokens": args.max_tokens,
        "budget_tokens": args.budget_tokens,
        "max_history_chars": args.max_history_chars,
        "history_policy": (
            "uniform across baselines: keep system + recent turns; drop oldest "
            "user+assistant pairs when estimated history chars exceed budget"
        ),
        "rep": args.rep,
        "baselines": baselines,
        "baseline_rotation": "offset=(episode_index+rep)%N; recorded per step",
        "episodes": [e["id"] for e in episodes],
        "config_digest": cfg.digest(),
        "env": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "dependencies": dep_versions(),
            "hardware": hardware_info(),
        },
        "capabilities": CAPABILITY_NOTES,
        "frozen_rules": tasks.get("frozen_rules", []),
        "timing_definitions": {
            "t_initial_sync_ms": "episode-level index/memory build sync; once; "
                                 "not included in any t_step_ms",
            "t_sync_ms": "in-step incremental sync",
            "t_route_ms": "P0 route_repo call",
            "t_assemble_ms": "context assembly only",
            "t_model_ms": "HTTP request wall time (network+queue+prefill+gen)",
            "t_eval_ms": "isolated pytest subprocess",
            "t_step_ms": "one step: in-step sync..eval + artifact writes",
            "t_episode_ms": "t_initial_sync_ms + sum(t_step_ms)",
        },
    })

    all_rows: list[dict] = []
    summaries: list[dict] = []
    orders_log: list[dict] = []
    for ep_idx, ep in enumerate(episodes):
        order, off = rotation_order(baselines, ep_idx, args.rep)
        orders_log.append(
            {"episode": ep["id"], "episode_index": ep_idx,
             "offset": off, "order": order}
        )
        print(f"[episode] {ep['id']} baseline_order={order} (offset={off})")
        for order_index, baseline in enumerate(order):
            print(f"[run] episode={ep['id']} baseline={baseline} ...")
            rows, summary = run_episode_baseline(
                episode=ep, baseline=baseline, out_dir=out_dir,
                model=args.model, endpoint=args.endpoint, args=args, cfg=cfg,
                rep=args.rep, order_index=order_index,
            )
            all_rows.extend(rows)
            summaries.append(summary)
            print(
                f"    steps={summary['steps']} passed={summary['steps_passed']}/"
                f"{summary['steps_evaluated']} "
                f"init_sync={summary['t_initial_sync_ms']}ms "
                f"mean_tokens={summary['mean_total_tokens']} "
                f"mean_model_ms={summary['mean_model_ms']}"
                + (f" errors={len(summary['errors'])}" if summary["errors"] else "")
            )

    write_csv(out_dir / "per_step.csv", all_rows, CSV_FIELDS)
    summary_fields = [
        "episode", "baseline", "rep", "baseline_order_index", "model",
        "steps", "steps_evaluated", "steps_passed",
        "t_initial_sync_ms", "t_episode_ms", "t_steps_sum_ms",
        "mean_total_tokens", "mean_prompt_tokens",
        "mean_model_ms", "mean_system_ms", "mean_step_ms",
        "reuse_omitted_total", "reuse_decisions_total",
        "reuse_omitted_bytes_total", "history_pairs_dropped_total", "errors",
    ]
    for s in summaries:
        s["errors"] = len(s["errors"])
    write_csv(out_dir / "summary.csv", summaries, summary_fields)
    write_json(out_dir / "baseline_orders.json", orders_log)
    write_json(out_dir / "run_complete.json", {
        "finished_at": now_iso(),
        "steps": len(all_rows),
        "summaries": summaries,
    })
    print(f"\nresults -> {out_dir}")
    return 0


def load_tasks(tasks_path: Path) -> dict:
    return json.loads(tasks_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
