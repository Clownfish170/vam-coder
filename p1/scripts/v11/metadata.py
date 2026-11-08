"""MemoryRecord 投影与注入前校验（hash / version / dependency）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VerifyResult:
    ok: bool
    action: str  # EXPAND | OMIT | INSUFFICIENT
    reason: str
    checks: dict


def verify_symbol_injection(
    *,
    entry: dict,
    workspace_sha: str | None,
    visible_sha: str | None,
    validity: str,
) -> VerifyResult:
    """单符号注入/省略前校验。

    entry 需含 symbol_id, content_hash/source_hash, version（可选）。
    """
    checks = {
        "symbol_id": entry.get("symbol_id"),
        "validity": validity,
        "hash_match_workspace": None,
        "visible_hash_match": None,
        "version": entry.get("version"),
    }
    desired = entry.get("source_hash") or entry.get("content_hash")
    if workspace_sha is not None and desired is not None:
        checks["hash_match_workspace"] = workspace_sha == desired
    if visible_sha is not None and desired is not None:
        checks["visible_hash_match"] = visible_sha == desired

    if validity == "tombstoned":
        return VerifyResult(False, "OMIT", "tombstoned_symbol_not_injected", checks)
    if validity in ("stale", "unverified"):
        return VerifyResult(True, "EXPAND", f"validity={validity}_force_expand", checks)
    if workspace_sha is not None and desired is not None and workspace_sha != desired:
        return VerifyResult(True, "EXPAND", "workspace_hash_mismatch", checks)
    if visible_sha is not None and desired is not None and visible_sha != desired:
        return VerifyResult(True, "EXPAND", "visible_hash_mismatch", checks)
    return VerifyResult(True, "EXPAND", "default_expand_or_assembler_downgrades", checks)


def project_records(entries: list) -> list[dict]:
    """L0 → L1 轻量投影（默认不注入；供审计）。"""
    out = []
    for e in entries:
        if hasattr(e, "symbol_id"):
            out.append(
                {
                    "symbol_id": e.symbol_id,
                    "file_path": getattr(e, "file_path", ""),
                    "type": getattr(e, "kind", ""),
                    "version": getattr(e, "version", None),
                    "content_hash": getattr(e, "content_hash", None),
                    "validity": getattr(e, "validity", None),
                    "dependencies": list(getattr(e, "deps", []) or []),
                }
            )
        elif isinstance(e, dict):
            out.append(
                {
                    "symbol_id": e.get("symbol_id"),
                    "file_path": e.get("file_path"),
                    "type": e.get("kind"),
                    "version": e.get("version"),
                    "content_hash": e.get("content_hash") or e.get("source_hash"),
                    "validity": e.get("validity"),
                    "dependencies": e.get("deps") or e.get("dependencies") or [],
                }
            )
    return out
