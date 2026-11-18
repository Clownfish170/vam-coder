"""引用解析与正文展开（纯函数为主）。

失败一律抛 CrResolveError；调用方回退磁盘 FULL，禁止静默忽略。
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Literal

from .store import MemoryStore, pin_sha256

RangeKind = Literal["full", "lines", "symbol"]
Purpose = Literal["must", "related", "background"]
RefKind = Literal["content", "slot"]


class CrResolveError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


@dataclass
class Reference:
    """R：指向 C 的钉扎引用（不单独进入模型，除非已展开）。"""

    path: str  # 工作区相对路径（磁盘回退 / FILE 块）
    purpose: Purpose = "related"
    ref_kind: RefKind = "content"
    content_id: str = ""
    slot_id: str = ""
    version: int | None = None
    pin_sha256: str = ""
    range_kind: RangeKind = "full"
    line_start: int | None = None
    line_end: int | None = None
    symbol: str | None = None
    deps: list[str] = field(default_factory=list)  # content_id 列表

    def audit(self) -> dict:
        return {
            "path": self.path,
            "purpose": self.purpose,
            "ref_kind": self.ref_kind,
            "content_id": self.content_id,
            "slot_id": self.slot_id,
            "version": self.version,
            "pin_sha256": self.pin_sha256[:16] if self.pin_sha256 else "",
            "range": self.range_kind,
            "symbol": self.symbol,
            "deps": list(self.deps),
        }


_WORD = r"(?<![A-Za-z0-9_]){name}(?![A-Za-z0-9_])"


def _boundary_hit(name: str, instruction: str) -> bool:
    if not name or len(name) < 2:
        return False
    return bool(
        re.search(_WORD.format(name=re.escape(name)), instruction or "")
    )


def slice_body(body: str, ref: Reference) -> str:
    """按 range 切片；非法 range → ILLEGAL_RANGE。"""
    if ref.range_kind == "full":
        return body
    lines = body.splitlines(keepends=True)
    if ref.range_kind == "lines":
        if ref.line_start is None or ref.line_end is None:
            raise CrResolveError("ILLEGAL_RANGE", "lines requires start/end")
        a, b = ref.line_start, ref.line_end
        if a < 1 or b < a or b > max(1, len(lines)):
            raise CrResolveError("ILLEGAL_RANGE", f"{a}-{b} n={len(lines)}")
        return "".join(lines[a - 1 : b])
    if ref.range_kind == "symbol":
        if not ref.symbol:
            raise CrResolveError("ILLEGAL_RANGE", "symbol requires name")
        # 在 body 内找 def/class 符号段（确定性 AST，失败则词界首段）
        try:
            tree = ast.parse(body)
        except SyntaxError as e:
            raise CrResolveError("ILLEGAL_RANGE", f"symbol parse:{e.msg}") from e
        for node in tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) and node.name == ref.symbol:
                seg = ast.get_source_segment(body, node)
                if seg is None:
                    raise CrResolveError("ILLEGAL_RANGE", "null segment")
                return seg if seg.endswith("\n") else seg + "\n"
        raise CrResolveError("ILLEGAL_RANGE", f"symbol not found:{ref.symbol}")
    raise CrResolveError("ILLEGAL_RANGE", ref.range_kind)


def resolve_ref(ref: Reference, store: MemoryStore) -> str:
    """解析 R → 正文（含 range）。禁止静默失败。"""
    if ref.ref_kind == "content":
        if not ref.content_id:
            raise CrResolveError("NOT_FOUND", "empty content_id")
        unit = store.get(ref.content_id)
        if unit is None:
            raise CrResolveError("NOT_FOUND", ref.content_id)
        if not unit.integrity_ok():
            raise CrResolveError("HASH_MISMATCH", ref.content_id)
        if ref.pin_sha256 and unit.pin_sha256 != ref.pin_sha256:
            raise CrResolveError("HASH_MISMATCH", ref.content_id)
        if ref.pin_sha256 and pin_sha256(unit.body_norm) != ref.pin_sha256:
            raise CrResolveError("HASH_MISMATCH", ref.content_id)
        return slice_body(unit.body_norm, ref)

    # slot 钉扎
    if not ref.slot_id:
        raise CrResolveError("UNKNOWN_SLOT", "empty slot_id")
    if ref.version is None:
        raise CrResolveError("VERSION_NOT_FOUND", "version pin required")
    slot = store.get_slot(ref.slot_id)
    if slot is None:
        raise CrResolveError("UNKNOWN_SLOT", ref.slot_id)
    ent = slot.history.get(ref.version)
    if ent is None:
        raise CrResolveError("VERSION_NOT_FOUND", f"{ref.slot_id}@{ref.version}")
    cid, sha = ent
    unit = store.get(cid)
    if unit is None:
        raise CrResolveError("NOT_FOUND", cid)
    if unit.pin_sha256 != sha:
        raise CrResolveError("HASH_MISMATCH", cid)
    if ref.pin_sha256 and ref.pin_sha256 != sha:
        raise CrResolveError("HASH_MISMATCH", cid)
    # 临时用 content 视图切片
    tmp = Reference(
        path=ref.path,
        purpose=ref.purpose,
        ref_kind="content",
        content_id=cid,
        pin_sha256=sha,
        range_kind=ref.range_kind,
        line_start=ref.line_start,
        line_end=ref.line_end,
        symbol=ref.symbol,
    )
    return resolve_ref(tmp, store)


def compact_source(source: str, instruction: str = "") -> tuple[str, str]:
    """相关非目标紧凑表示。

    返回 (body, kind)。
    - AST 可解析：顶层 def/class/常量；指令词界命中 → 完整源段，否则**合法**签名桩。
    - 签名桩必须是可解析 Python（`...` 体），禁止 `def f():` 裸头——
      裸头会污染上下文并诱发 1.5B NO_EDIT（本地筛选实证）。
    - 解析失败：保守返回原文 kind=source_full（不丢信息）。
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return source, "source_full"
    parts: list[str] = []
    any_node = False
    for node in tree.body:
        any_node = True
        name = ""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            seg = ast.get_source_segment(source, node) or ""
            if _boundary_hit(name, instruction):
                body = seg.rstrip() + "\n"
                parts.append(body)
            else:
                # 合法桩：签名 + `...` 体（保持可 import/可解析）
                first = seg.splitlines()[0].rstrip() if seg else f"def {name}(...):"
                if not first.endswith(":"):
                    first = first + ":"
                parts.append(first + "\n    ...\n")
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    name = t.id
                    seg = ast.get_source_segment(source, node) or ""
                    if _boundary_hit(name, instruction):
                        parts.append(seg.rstrip() + "\n")
                    else:
                        line = seg.splitlines()[0].rstrip() if seg else f"{name} = ..."
                        parts.append(line + "\n")
                    break
        elif isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr)):
            seg = ast.get_source_segment(source, node)
            if seg:
                parts.append(seg.rstrip() + "\n")
    if not any_node:
        return source, "source_full"
    if not parts:
        return source, "source_full"
    body = "".join(parts)
    if not body.endswith("\n"):
        body += "\n"
    # 桩后自检：必须仍是合法 Python；否则回退全文
    try:
        ast.parse(body)
    except SyntaxError:
        return source, "source_full"
    return body, "signature"


def mem_block(content_id: str, kind: str, body: str, *, path: str = "") -> str:
    """Prompt 文本标记 + **始终附带展开正文**（禁止裸 ID）。"""
    body = body.rstrip("\n")
    return (
        f"--- MEM id={content_id} kind={kind} range=full path={path} ---\n"
        f"{body}\n"
    )


def file_block(rel: str, content: str) -> str:
    """与 assemble 一致的 FILE 块（E/C/must 专用）。"""
    return f"--- FILE {rel} (full current source) ---\n{content.rstrip()}\n"
