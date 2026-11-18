"""四层校验中的 Memory / Reference / Dependency（Final Visibility 仍走既有 pre_send）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .resolver import CrResolveError, Reference, resolve_ref
from .store import MemoryStore


@dataclass
class CrCheck:
    ok: bool = True
    memory_ok: bool = True
    reference_ok: bool = True
    dependency_ok: bool = True
    codes: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    # 解析成功的 path → 交付 content_id（供审计）
    resolved: dict[str, str] = field(default_factory=dict)

    def fail(self, code: str, detail: str = "") -> None:
        self.ok = False
        if code.startswith("MEM_"):
            self.memory_ok = False
        elif code.startswith("REF_") or code in (
            "NOT_FOUND",
            "HASH_MISMATCH",
            "UNKNOWN_SLOT",
            "VERSION_NOT_FOUND",
            "ILLEGAL_RANGE",
        ):
            self.reference_ok = False
        elif code.startswith("DEP_"):
            self.dependency_ok = False
        tag = code if not detail else f"{code}:{detail}"
        if tag not in self.codes:
            self.codes.append(tag)
        if detail:
            self.details.append(tag)


def validate_cr(
    refs: list[Reference],
    store: MemoryStore,
    *,
    required_paths: set[str] | None = None,
    delivered_paths: set[str] | None = None,
) -> CrCheck:
    """Memory + Reference + Dependency 完整性。

    - Memory：引用的 C 必须 integrity_ok
    - Reference：resolve_ref 成功；失败不静默
    - Dependency：required_paths（must/ET/C）⊆ delivered_paths ∪ 本步 resolve 成功集
      （装配后调用方传入最终 delivered；此处对 refs 内 path 做引用闭包检查）
    """
    check = CrCheck()
    delivered = set(delivered_paths or ())
    required = set(required_paths or ())

    for ref in refs:
        # Memory / Reference
        if ref.ref_kind == "content" and ref.content_id:
            unit = store.get(ref.content_id)
            if unit is None:
                check.fail("MEM_NOT_FOUND", ref.content_id)
                continue
            if not unit.integrity_ok():
                check.fail("MEM_INTEGRITY", ref.content_id)
                continue
            if ref.pin_sha256 and unit.pin_sha256 != ref.pin_sha256:
                check.fail("MEM_PIN_MISMATCH", ref.content_id)
                continue
        try:
            body = resolve_ref(ref, store) if (
                ref.content_id or (ref.slot_id and ref.version is not None)
            ) else None
        except CrResolveError as e:
            # 无 content_id 的 must 磁盘引用允许（装配走磁盘）；有 id 的必须可解析
            if ref.content_id or ref.ref_kind == "slot":
                check.fail(e.code, e.detail if hasattr(e, "detail") else str(e))
            body = None
        if body is not None:
            check.resolved[ref.path] = ref.content_id or check.resolved.get(ref.path, "")

    # Dependency：required 必须出现在 delivered（最终 messages 将含这些路径的正文）
    # 调用方在装配后传入 delivered_paths；required 非空即检查（delivered 可为空）
    if required:
        delivered_or_resolved = delivered | set(check.resolved)
        missing = required - delivered_or_resolved
        for m in sorted(missing):
            check.fail("DEP_INCOMPLETE", m)

    if not check.ok and not check.codes:
        check.fail("REF_DANGLING", "unknown")
    return check
