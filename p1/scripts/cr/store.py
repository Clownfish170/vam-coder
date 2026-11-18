"""内容寻址记忆存储（C 单元 + Slot）。

确定性：Normalize + blake3 → content_id；相同正文 → 相同 ID。
禁止原地改写已存在单元的 body_norm。
"""

from __future__ import annotations

import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any

try:
    from blake3 import blake3 as _blake3
except ImportError:  # pragma: no cover
    import hashlib

    def _blake3(data: bytes) -> Any:  # type: ignore[misc]
        return hashlib.blake2b(data, digest_size=32)


class CrStoreError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def normalize_body(raw: str) -> str:
    """规范化：去 BOM、CRLF→LF、行尾空白 strip、NFC、末尾单换行。"""
    if raw is None:
        raise CrStoreError("EMPTY_BODY", "raw is None")
    s = raw
    if s.startswith("﻿"):
        s = s[1:]
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = unicodedata.normalize("NFC", s)
    lines = [ln.rstrip() for ln in s.split("\n")]
    # 去尾部多余空行，保留内容结构
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _digest_hex(data: bytes) -> str:
    h = _blake3(data)
    if hasattr(h, "hexdigest"):
        return h.hexdigest()
    return h.hexdigest()  # type: ignore[union-attr]


def pin_sha256(body_norm: str) -> str:
    """正文钉扎哈希（blake3-256 hex；与 content_id 同源算法）。"""
    return _digest_hex(body_norm.encode("utf-8"))


def content_id_of(body_norm: str) -> str:
    """content_id := C: + blake3(body_norm) 前 12 hex（48-bit）。"""
    return "C:" + pin_sha256(body_norm)[:12]


@dataclass
class MemoryUnit:
    content_id: str
    body_norm: str
    kind: str  # source_full | source_symbol | signature | decision | digest
    pin_sha256: str
    origin: dict = field(default_factory=dict)
    deps: list[str] = field(default_factory=list)
    created_at: float = 0.0
    meta: dict = field(default_factory=dict)

    def integrity_ok(self) -> bool:
        return pin_sha256(self.body_norm) == self.pin_sha256


@dataclass
class Slot:
    slot_id: str
    # version -> (content_id, pin_sha256)
    history: dict[int, tuple[str, str]] = field(default_factory=dict)
    current_version: int = 0


class MemoryStore:
    """进程内内容寻址库；可选落盘由调用方序列化。"""

    def __init__(self) -> None:
        self._units: dict[str, MemoryUnit] = {}
        self._slots: dict[str, Slot] = {}

    def __len__(self) -> int:
        return len(self._units)

    def put_raw(
        self,
        raw: str,
        *,
        kind: str = "source_full",
        origin: dict | None = None,
        deps: list[str] | None = None,
        meta: dict | None = None,
        allow_empty: bool = False,
    ) -> tuple[MemoryUnit, bool]:
        """Normalize+Dedup。返回 (unit, hit)。

        hit=True：已存在同 content_id 且 pin 一致。
        碰撞（同 id 不同 pin）→ ID_COLLISION。
        """
        body = normalize_body(raw)
        if not body and not allow_empty:
            if kind == "source_full":
                raise CrStoreError("EMPTY_BODY", "source_full requires non-empty body")
            allow_empty = True  # signature 等允许空则继续
        cid = content_id_of(body) if body else "C:" + ("0" * 12)
        pin = pin_sha256(body) if body else "0" * 64
        existing = self._units.get(cid)
        if existing is not None:
            if existing.pin_sha256 != pin:
                raise CrStoreError("ID_COLLISION", cid)
            return existing, True
        unit = MemoryUnit(
            content_id=cid,
            body_norm=body,
            kind=kind,
            pin_sha256=pin,
            origin=dict(origin or {}),
            deps=list(deps or []),
            created_at=time.time(),
            meta=dict(meta or {}),
        )
        self._units[cid] = unit
        return unit, False

    def get(self, content_id: str) -> MemoryUnit | None:
        return self._units.get(content_id)

    def get_slot(self, slot_id: str) -> Slot | None:
        return self._slots.get(slot_id)

    def create_slot(self, slot_id: str) -> Slot:
        if slot_id in self._slots:
            raise CrStoreError("SLOT_EXISTS", slot_id)
        slot = Slot(slot_id=slot_id)
        self._slots[slot_id] = slot
        return slot

    def update_slot(
        self,
        slot_id: str,
        new_raw: str,
        *,
        kind: str = "source_full",
        origin: dict | None = None,
        auto_create: bool = False,
    ) -> tuple[Slot, MemoryUnit]:
        slot = self._slots.get(slot_id)
        if slot is None:
            if not auto_create:
                raise CrStoreError("UNKNOWN_SLOT", slot_id)
            slot = self.create_slot(slot_id)
        unit, _ = self.put_raw(new_raw, kind=kind, origin=origin)
        ver = slot.current_version + 1
        slot.history[ver] = (unit.content_id, unit.pin_sha256)
        slot.current_version = ver
        return slot, unit

    def integrity_check(self, content_id: str) -> bool:
        u = self._units.get(content_id)
        if u is None:
            return False
        return u.integrity_ok()
