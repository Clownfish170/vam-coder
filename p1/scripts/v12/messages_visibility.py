"""发送前消息可见性强制验证（阶段 B）。

O′ 最终授权仅来自「当前请求最终 messages 中完整 FILE 块 + SHA256 一致」。
不得单独依赖 episode 级 tracker / 曾装配上下文。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from v11.visibility import _norm_path, content_sha256

_ASSIST_FILE_RE = re.compile(
    r"FILE:\s*(?P<path>[^\n]+)\n```[^\n]*\n(?P<body>[\s\S]*?)```"
)
# 在 --- FILE … --- 之后，body 停在下一个 --- 块或 === 段之前（build_messages 会拼 OUTPUT FORMAT）
_CTX_FILE_RE = re.compile(
    r"--- FILE (?P<path>[^\n(]+) \(full current source\) ---\n"
    r"(?P<body>[\s\S]*?)"
    r"(?=\n--- (?:FILE|INDEX) |\n=== |\Z)"
)


def full_files_in_messages(messages: list[dict]) -> dict[str, str]:
    """从最终 messages 提取完整源码：assistant FILE 围栏 + user CONTEXT FILE 块。

    返回 relpath -> 归一化 body（用于 content_sha256）。
    """
    out: dict[str, str] = {}
    for m in messages or []:
        role = m.get("role")
        content = m.get("content") or ""
        if role == "assistant":
            for mo in _ASSIST_FILE_RE.finditer(content):
                out[_norm_path(mo.group("path"))] = mo.group("body")
        elif role == "user":
            for mo in _CTX_FILE_RE.finditer(content):
                out[_norm_path(mo.group("path"))] = mo.group("body")
    return out


def current_context_files(messages: list[dict]) -> dict[str, str]:
    """仅最后一条 user 消息中的 CONTEXT FILE（本轮注入），不含历史 assistant。"""
    for m in reversed(list(messages or [])):
        if m.get("role") == "user":
            content = m.get("content") or ""
            out: dict[str, str] = {}
            for mo in _CTX_FILE_RE.finditer(content):
                out[_norm_path(mo.group("path"))] = mo.group("body")
            return out
    return {}


@dataclass
class PreSendCheck:
    ok: bool
    missing_or_mismatch: list[str]
    visible_hashes: dict[str, str]
    reasons: dict[str, str]
    edit_target_full_verified: bool = True
    candidate_full_verified: bool = True
    edit_target_missing: list[str] | None = None
    candidate_missing: list[str] | None = None


def verify_omissions_in_messages(
    messages: list[dict],
    omitted_files: list[str],
    disk_sha: dict[str, str],
    *,
    edit_targets: list[str] | None = None,
    candidate_full: list[str] | None = None,
) -> PreSendCheck:
    """O′ 省略：须在最终 messages 全文可见且 hash=disk。

    E/C（r2.2）：必须在 **当前 user CONTEXT** 完整 FILE 且 hash=disk
    （历史 assistant 不算）。
    """
    visible = full_files_in_messages(messages)
    current_ctx = current_context_files(messages)
    vis_hash = {rel: content_sha256(body) for rel, body in visible.items()}
    bad: list[str] = []
    reasons: dict[str, str] = {}

    def _check_map(pool: dict[str, str], rel: str) -> str | None:
        rel = _norm_path(rel)
        if rel not in pool:
            return "not_in_current_context" if pool is current_ctx else "not_in_final_messages"
        want = disk_sha.get(rel)
        got = content_sha256(pool[rel])
        if want is None:
            return "disk_sha_unknown"
        if got != want:
            return f"hash_mismatch visible={got} disk={want}"
        return None

    for rel in omitted_files or []:
        rel_n = _norm_path(rel)
        if rel_n not in visible:
            bad.append(rel_n)
            reasons[rel_n] = "not_in_final_messages"
            continue
        want = disk_sha.get(rel_n)
        got = vis_hash.get(rel_n)
        if want is None:
            bad.append(rel_n)
            reasons[rel_n] = "disk_sha_unknown"
        elif got != want:
            bad.append(rel_n)
            reasons[rel_n] = f"hash_mismatch visible={got} disk={want}"

    def _verify_ctx(items: list[str] | None) -> tuple[bool, list[str]]:
        missing: list[str] = []
        for rel in items or []:
            err = _check_map(current_ctx, rel)
            if err:
                missing.append(_norm_path(rel))
                reasons[_norm_path(rel)] = err
        return (not missing), missing

    et_ok, et_miss = _verify_ctx(edit_targets)
    cf_ok, cf_miss = _verify_ctx(candidate_full)

    return PreSendCheck(
        ok=not bad and et_ok and cf_ok,
        missing_or_mismatch=bad + et_miss + cf_miss,
        visible_hashes=vis_hash,
        reasons=reasons,
        edit_target_full_verified=et_ok,
        candidate_full_verified=cf_ok,
        edit_target_missing=et_miss,
        candidate_missing=cf_miss,
    )
