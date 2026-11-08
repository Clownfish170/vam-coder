"""对话可见性追踪：修复 V1.0 history_sent ≠ 当前 messages 的主因。

省略谓词 O′：
  hash_match ∧ previously_visible_in_messages ∧ file_not_in_current_ctx
  ∧ not_tombstoned_unsafe ∧ not_forced_expand
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field


_FILE_RE = re.compile(
    r"--- FILE (?P<path>[^\n(]+) \(full current source\) ---\n(?P<body>[\s\S]*?)(?=\n--- |\Z)"
)
_ASSIST_FILE_RE = re.compile(
    r"FILE:\s*(?P<path>[^\n]+)\n```[^\n]*\n(?P<body>[\s\S]*?)```"
)


def content_sha256(text: str) -> str:
    # 文件级归一化：CRLF→LF、统一尾部换行，避免 apply/围栏差异导致假阴性
    if text:
        text = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm_path(raw: str) -> str:
    return raw.strip().strip("`").strip('"').strip("'").replace("\\", "/")


@dataclass
class VisibilityProof:
    relpath: str
    content_hash: str
    where: str  # context | assistant | both
    n_chars: int

    def to_dict(self) -> dict:
        return {
            "relpath": self.relpath,
            "content_hash": self.content_hash,
            "where": self.where,
            "n_chars": self.n_chars,
        }


@dataclass
class VisibilityTracker:
    """记录“当前 messages 中仍可见”的完整文件内容哈希。

    与 V1.0 history_sent 的差异：只信任**实际拼进 messages 的文本**
    （当前步 context 或历史 assistant FILE 块），不信任“曾在 user 上下文
    发送过”的全局记账。
    """

    _files: dict[str, str] = field(default_factory=dict)  # relpath -> sha256
    _chars: dict[str, int] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def mark_from_context(self, context_text: str) -> list[VisibilityProof]:
        proofs: list[VisibilityProof] = []
        for m in _FILE_RE.finditer(context_text or ""):
            rel = _norm_path(m.group("path"))
            body = m.group("body")
            h = content_sha256(body)
            prev = self._files.get(rel)
            self._files[rel] = h
            self._chars[rel] = len(body)
            proofs.append(
                VisibilityProof(rel, h, "both" if prev == h else "context", len(body))
            )
        return proofs

    def mark_from_assistant(self, content: str) -> list[VisibilityProof]:
        proofs: list[VisibilityProof] = []
        for m in _ASSIST_FILE_RE.finditer(content or ""):
            rel = _norm_path(m.group("path"))
            body = m.group("body")
            h = content_sha256(body)
            prev = self._files.get(rel)
            self._files[rel] = h
            self._chars[rel] = len(body)
            proofs.append(
                VisibilityProof(rel, h, "both" if prev == h else "assistant", len(body))
            )
        return proofs

    def has_visible(self, relpath: str, content_sha: str | None = None) -> bool:
        rel = _norm_path(relpath)
        if rel not in self._files:
            return False
        if content_sha is None:
            return True
        return self._files[rel] == content_sha

    def proof(self, relpath: str) -> VisibilityProof | None:
        rel = _norm_path(relpath)
        if rel not in self._files:
            return None
        return VisibilityProof(rel, self._files[rel], "tracked", self._chars.get(rel, 0))

    def visible_paths(self) -> list[str]:
        return sorted(self._files)

    def snapshot(self) -> dict[str, str]:
        return dict(self._files)


def visible_file_blocks(messages: list[dict]) -> dict[str, str]:
    """从 messages 提取仍可见的 FILE 内容（assistant + 当前 user context）。"""
    out: dict[str, str] = {}
    for m in messages:
        content = m.get("content") or ""
        if m.get("role") == "assistant":
            for match in _ASSIST_FILE_RE.finditer(content):
                out[_norm_path(match.group("path"))] = match.group("body")
        elif m.get("role") == "user" and "=== CONTEXT ===" in content:
            for match in _FILE_RE.finditer(content):
                out[_norm_path(match.group("path"))] = match.group("body")
    return out


def safe_omission(
    *,
    relpath: str,
    desired_sha: str,
    tracker: VisibilityTracker,
    current_context_paths: set[str],
    validity: str,
    force_expand: bool,
) -> tuple[bool, list[str]]:
    """O′ 判定。返回 (allow_omit, reasons)。"""
    rel = _norm_path(relpath)
    reasons: list[str] = []
    if force_expand:
        reasons.append("force_expand")
    if validity == "tombstoned":
        reasons.append("validity=tombstoned")
    if rel in current_context_paths:
        reasons.append("already_in_current_context")
    if not tracker.has_visible(rel, desired_sha):
        reasons.append("no_visible_proof_in_messages")
    allow = not reasons
    if allow:
        reasons.append("O_prime=visible_hash_match")
    return allow, reasons
