"""V1.1 上下文装配：短 MODE + 文件块与 memory_off 同构 + O′ 安全省略。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .visibility import VisibilityTracker, content_sha256, safe_omission


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


@dataclass
class AssembledV11:
    text: str
    file_blocks: int = 0
    injected_chars: int = 0
    omitted_files: list[str] = field(default_factory=list)
    omitted_chars_est: int = 0
    verified_safe_omissions: int = 0
    fallback_events: int = 0
    insufficient: bool = False
    audits: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # 兼容 v1.0 字段名（便于 CSV 超集）
    reuse_omitted: int = 0
    reuse_omitted_files: int = 0
    reuse_omitted_bytes: int = 0
    expand_included_bytes: int = 0
    n_verified_safe_omissions: int = 0
    assemble_audit: list = field(default_factory=list)
    summary_blocks: int = 0
    summary_bytes: int = 0


def assemble_vam_v11(
    workspace: Path,
    plan_files: list,
    tracker: VisibilityTracker,
    *,
    mode_banner: str = "short",
    chars_per_token: int = 4,
) -> AssembledV11:
    """按 RetrievePlan.files 装配。

    mode_banner: none | short | long（long 仅消融；默认 short 极短行）。
    REUSE_KV 仅在 O′ 通过时省略，否则升为 EXPAND（记录 fallback）。
    """
    ws_files = _read_files(workspace)
    current_paths: set[str] = set()
    parts: list[str] = []
    if mode_banner == "short":
        parts.append("[ctx] v1.1")
    elif mode_banner == "long":
        parts.append(
            "[MODE] vam_coder_v1.1: visibility-safe reuse "
            "(omit only when exact content is visible in this conversation)."
        )
    # none → 不加 banner

    ctx = AssembledV11(text="")
    sha_map = {rel: content_sha256(text) for rel, text in ws_files.items()}

    for fp in plan_files:
        rel = _posix(fp.relpath)
        action = getattr(fp, "action", "EXPAND")
        validity = getattr(fp, "validity", "valid")
        desired = getattr(fp, "content_sha256", None) or sha_map.get(rel)
        content = ws_files.get(rel)
        if content is None:
            # 磁盘缺失：不伪造源码
            ctx.insufficient = True
            ctx.fallback_events += 1
            ctx.notes.append(f"missing_file:{rel}")
            ctx.audits.append(
                {
                    "file": rel,
                    "action": "INSUFFICIENT",
                    "verified_safe_omission": False,
                    "reason": "file_missing_on_disk",
                }
            )
            continue

        if action == "DROP" and validity == "tombstoned":
            ctx.audits.append(
                {
                    "file": rel,
                    "action": "DROP",
                    "verified_safe_omission": False,
                    "reason": "tombstoned",
                }
            )
            continue

        if action == "REUSE_KV":
            allow, reasons = safe_omission(
                relpath=rel,
                desired_sha=desired or content_sha256(content),
                tracker=tracker,
                current_context_paths=current_paths,
                validity=validity,
                force_expand=False,
            )
            if allow:
                nbytes = len(content.encode("utf-8"))
                ctx.omitted_files.append(rel)
                ctx.omitted_chars_est += nbytes
                ctx.verified_safe_omissions += 1
                ctx.reuse_omitted += 1
                ctx.reuse_omitted_files += 1
                ctx.reuse_omitted_bytes += nbytes
                ctx.audits.append(
                    {
                        "file": rel,
                        "action": "REUSE_KV",
                        "verified_safe_omission": True,
                        "reasons": reasons,
                        "omitted_bytes": nbytes,
                        "omitted_tokens_est": nbytes // max(1, chars_per_token),
                    }
                )
                ctx.assemble_audit.append(
                    {
                        "file": rel,
                        "verified_safe_omission": True,
                        "omitted_bytes": nbytes,
                        "omitted_tokens_est": nbytes // max(1, chars_per_token),
                        "reasons": reasons,
                    }
                )
                continue
            # O′ 失败 → 回退 EXPAND
            ctx.fallback_events += 1
            ctx.notes.append(f"fallback_expand:{rel}:{','.join(reasons)}")
            action = "EXPAND"

        # EXPAND
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
                "reason": getattr(fp, "reason", ""),
                "included_bytes": nbytes,
            }
        )

    ctx.n_verified_safe_omissions = ctx.verified_safe_omissions
    ctx.text = "\n".join(parts) + "\n" if parts else "\n"
    # 装配后立刻把注入内容标为可见
    tracker.mark_from_context(ctx.text)
    return ctx
