"""V1.2 上下文装配：Full / Digest / NONE + O′ 安全省略 + 窗口保护。

V1.3A_CR：相关非目标在 O′ 不可省略时，可改为 MEM 紧凑展开（cr_enabled）。
E/C/must 始终 FILE 整文件；禁止裸 ID。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from v11.visibility import VisibilityTracker, content_sha256, safe_omission

from .config import AblationConfig
from .levels import ExpandPlan, FileLevel


def _posix(p: str) -> str:
    return str(p).replace("\\", "/")


def _read_files(workspace: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for p in sorted(Path(workspace).rglob("*.py")):
        rel = _posix(p.relative_to(workspace))
        if rel.startswith("eval/") or "/__pycache__/" in f"/{rel}":
            continue
        try:
            files[rel] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return files


def _file_block(rel: str, content: str) -> str:
    return f"--- FILE {rel} (full current source) ---\n{content.rstrip()}\n"


def _digest_line(rel: str, content: str, symbols: list[str] | None = None) -> str:
    fns = ",".join(symbols[:6]) if symbols else ""
    # ~短行，控制 token
    if fns:
        return f"--- INDEX {rel} [{fns}] ---"
    return f"--- INDEX {rel} ---"


@dataclass
class AssembledV12:
    text: str
    file_blocks: int = 0
    digest_lines: int = 0
    injected_chars: int = 0
    omitted_files: list[str] = field(default_factory=list)
    omitted_chars_est: int = 0
    verified_safe_omissions: int = 0
    insufficient: bool = False
    insufficient_reasons: list[str] = field(default_factory=list)
    required_context_tokens_est: int | None = None
    available_context_tokens: int | None = None
    audits: list[dict] = field(default_factory=list)
    assemble_audit: list = field(default_factory=list)
    expand_included_bytes: int = 0
    reuse_omitted_files: int = 0
    reuse_omitted_bytes: int = 0
    n_verified_safe_omissions: int = 0
    summary_blocks: int = 0
    notes: list[str] = field(default_factory=list)
    # V1.3A_CR
    mem_blocks: int = 0
    cr_refs: list[dict] = field(default_factory=list)
    cr_store: object | None = None
    cr_expanded_paths: list[str] = field(default_factory=list)


def assemble_v12(
    workspace: Path,
    plan: ExpandPlan,
    tracker: VisibilityTracker,
    cfg: AblationConfig,
    *,
    symbols_by_file: dict[str, list[str]] | None = None,
    system_history_tokens_est: int = 0,
    force_full: set[str] | None = None,
    record_context_marks: bool = False,
    cr_store: object | None = None,
    cr_instruction: str = "",
    slow_store: object | None = None,
) -> AssembledV12:
    """按计划装配。

    tracker：O′ **候选**证明（应由 proof.tracker_from_history 从 trim 后历史构建）。
    force_full：预检失败后必须 FULL 的路径（跳过 O′）。
    record_context_marks：默认 False——**不再**把本步 context 写入 tracker 作为跨步授权
    （P0 缺陷修复；诊断可显式打开）。
    cr_store：V1.3A_CR 内容寻址库；cfg.cr_enabled=False 时忽略。
    slow_store：V13D 慢层；sha 一致时 related 可注入已验证紧凑正文。
    """
    symbols_by_file = symbols_by_file or {}
    force_full = {_posix(p) for p in (force_full or set())}
    ws_files = _read_files(workspace)
    # 头部等长化（V13B 轮测量修正）：所有经 v12 装配的臂共用同一行，
    # 避免臂名长度差污染 prompt_tokens 配对比较；臂身份记录于 audit/run_meta。
    parts: list[str] = ["[ctx]"]
    ctx = AssembledV12(text="")
    ctx.insufficient = plan.insufficient
    ctx.insufficient_reasons = list(plan.insufficient_reasons)
    ctx.required_context_tokens_est = plan.required_context_tokens_est
    ctx.available_context_tokens = plan.available_context_tokens

    cr_on = bool(getattr(cfg, "cr_enabled", False)) and cr_store is not None
    cr_mode = str(getattr(cfg, "cr_related_mode", "full"))
    if cr_on:
        ctx.cr_store = cr_store
        ctx.notes.append(f"cr_enabled:mode={cr_mode}")
    slow_on = bool(getattr(cfg, "slow_enabled", False)) and slow_store is not None
    if slow_on:
        ctx.notes.append("slow_enabled")

    current_paths: set[str] = set()
    for fl in plan.files:
        rel = _posix(fl.relpath)
        content = ws_files.get(rel)
        if fl.level == "NONE":
            ctx.audits.append(
                {"file": rel, "action": "NONE", "verified_safe_omission": False, "reason": fl.reason}
            )
            continue

        if content is None:
            if fl.is_must:
                ctx.insufficient = True
                if "MISSING_REQUIRED_FILE" not in ctx.insufficient_reasons:
                    ctx.insufficient_reasons.append("MISSING_REQUIRED_FILE")
                ctx.audits.append(
                    {
                        "file": rel,
                        "action": "INSUFFICIENT",
                        "verified_safe_omission": False,
                        "reason": "file_missing_on_disk",
                    }
                )
            continue

        desired = content_sha256(content)

        if fl.level == "DIGEST":
            line = _digest_line(rel, content, symbols_by_file.get(rel))
            parts.append(line)
            ctx.digest_lines += 1
            ctx.audits.append(
                {"file": rel, "action": "DIGEST", "verified_safe_omission": False, "reason": fl.reason}
            )
            continue

        # FULL：仅当 O′ 开启且非 force_full 且非 E/C 时尝试省略
        try_omit = (
            bool(cfg.o_prime)
            and (rel not in force_full)
            and not fl.is_edit_target
            and not (
                fl.is_candidate and getattr(cfg, "candidate_full_oprime_forbid", True)
            )
            and not (
                fl.is_edit_target and getattr(cfg, "edit_target_oprime_forbid", True)
            )
        )
        # 编辑目标在开关开启时禁止 O′
        if fl.is_edit_target and getattr(cfg, "edit_target_oprime_forbid", True):
            try_omit = False
        if fl.is_candidate and getattr(cfg, "candidate_full_oprime_forbid", True):
            try_omit = False
        if try_omit:
            allow, reasons = safe_omission(
                relpath=rel,
                desired_sha=desired,
                tracker=tracker,
                current_context_paths=current_paths,
                validity=fl.validity,
                force_expand=False,
            )
            if allow:
                nbytes = len(content.encode("utf-8"))
                ctx.omitted_files.append(rel)
                ctx.omitted_chars_est += nbytes
                ctx.verified_safe_omissions += 1
                ctx.reuse_omitted_files += 1
                ctx.reuse_omitted_bytes += nbytes
                ctx.audits.append(
                    {
                        "file": rel,
                        "action": "REUSE_KV",
                        "verified_safe_omission": True,
                        "reasons": reasons + ["phase_a_candidate_only"],
                        "omitted_bytes": nbytes,
                        "is_must": fl.is_must,
                    }
                )
                ctx.assemble_audit.append(
                    {
                        "file": rel,
                        "verified_safe_omission": True,
                        "omitted_bytes": nbytes,
                        "omitted_tokens_est": nbytes // max(1, cfg.chars_per_token),
                    }
                )
                continue

        # V1.3A_CR：相关非目标（非 must/ET/C）
        # 1.5B 实证：MEM/紧凑正文 → NO_EDIT；仅完整 FILE 或不注入可靠。
        # V13A：cr_related_mode=compact/none → O′ 失败后跳过注入。
        # V13B（迭代）：ICG 已在 plan 层把落选降为 NONE；
        #   入选 reason=icg_full 且 cr_related_mode=full → 走下方 FILE，不 skip。
        is_forced_full = (
            fl.is_must or fl.is_edit_target or fl.is_candidate or rel in force_full
        )
        is_icg_full = getattr(fl, "reason", "") == "icg_full"
        if (
            cr_on
            and not is_forced_full
            and fl.level == "FULL"
            and cr_mode in ("compact", "none", "full")
            and not is_icg_full
        ):
            # V13A blanket-skip（compact/none）；icg_full 或 full 模式不在此 skip
            if cr_mode in ("compact", "none"):
                try:
                    from cr.store import MemoryStore

                    store: MemoryStore = cr_store  # type: ignore[assignment]
                    try:
                        store.put_raw(
                            content,
                            kind="source_full",
                            origin={"file_path": rel, "role": "related_cache"},
                        )
                    except Exception:
                        pass
                    ctx.audits.append(
                        {
                            "file": rel,
                            "action": "CR_RELATED_SKIPPED",
                            "verified_safe_omission": False,
                            "reason": "related_non_target_not_injected",
                            "is_must": False,
                        }
                    )
                    ctx.notes.append(f"cr_skip_related:{rel}")
                    continue
                except Exception as e:  # fail-closed → 磁盘 FULL
                    ctx.notes.append(f"cr_fallback_full:{rel}:{type(e).__name__}:{e}")

        # V13A/V13B：入选或强制相关正文入库（内容寻址侧车）
        if cr_on and not is_forced_full and fl.level == "FULL" and cr_store is not None:
            try:
                from cr.store import MemoryStore

                st: MemoryStore = cr_store  # type: ignore[assignment]
                st.put_raw(
                    content,
                    kind="source_full",
                    origin={
                        "file_path": rel,
                        "role": "related_selected" if is_icg_full else "related_full",
                    },
                )
            except Exception:
                pass

        # V13D：慢层命中（sha 一致）→ 注入已验证紧凑正文（仍用 FILE 头，保持协议）
        if (
            slow_on
            and not is_forced_full
            and fl.level == "FULL"
            and fl.content_sha256
        ):
            try:
                from cr.slowmem import SlowStore

                sstore: SlowStore = slow_store  # type: ignore[assignment]
                unit = sstore.query(rel, fl.content_sha256)
                if unit is not None and unit.body_norm:
                    block = _file_block(rel, unit.body_norm)
                    parts.append(block)
                    current_paths.add(rel)
                    ctx.file_blocks += 1
                    nbytes = len(unit.body_norm.encode("utf-8"))
                    ctx.injected_chars += nbytes
                    ctx.expand_included_bytes += nbytes
                    ctx.audits.append(
                        {
                            "file": rel,
                            "action": "SLOW_EXPAND",
                            "verified_safe_omission": False,
                            "content_id": unit.content_id,
                            "origin": unit.origin,
                            "included_bytes": nbytes,
                            "is_must": False,
                        }
                    )
                    ctx.notes.append(f"slow_hit:{rel}")
                    continue
            except Exception as e:  # fail-closed → 磁盘 FULL
                ctx.notes.append(f"slow_fallback:{rel}:{type(e).__name__}")

        parts.append(_file_block(rel, content))
        current_paths.add(rel)
        ctx.file_blocks += 1
        nbytes = len(content.encode("utf-8"))
        ctx.injected_chars += nbytes
        ctx.expand_included_bytes += nbytes
        ctx.audits.append(
            {
                "file": rel,
                "action": "EXPAND",
                "verified_safe_omission": False,
                "is_must": fl.is_must,
                "included_bytes": nbytes,
                "forced": rel in force_full,
            }
        )

    ctx.n_verified_safe_omissions = ctx.verified_safe_omissions
    ctx.text = "\n".join(parts) + "\n"
    if plan.required_context_tokens_est and plan.required_context_tokens_est > cfg.context_window:
        ctx.insufficient = True
        if "REQUIRED_CONTEXT_EXCEEDS_LIMIT" not in ctx.insufficient_reasons:
            ctx.insufficient_reasons.append("REQUIRED_CONTEXT_EXCEEDS_LIMIT")
        ctx.required_context_tokens_est = plan.required_context_tokens_est
        ctx.available_context_tokens = cfg.context_window

    # 默认不把本步 context 写入跨步授权 tracker（修复 P0）
    if record_context_marks:
        tracker.mark_from_context(ctx.text)
    return ctx
