"""Select：由 ExpandPlan 生成 Reference 集合（不改 E/C/must 定义）。"""

from __future__ import annotations

from v12.config import AblationConfig
from v12.levels import ExpandPlan

from .resolver import Reference
from .store import MemoryStore, normalize_body


def select_refs(
    plan: ExpandPlan,
    cfg: AblationConfig,
    *,
    disk_files: dict[str, str],
    store: MemoryStore | None = None,
) -> list[Reference]:
    """强制层走磁盘 FULL 语义（purpose=must）；相关非目标按 cr_related_mode。

    store 非空时为相关非目标预注册 content 引用（正文仍以磁盘为准装配）。
    """
    refs: list[Reference] = []
    seen: set[str] = set()

    def _add(ref: Reference) -> None:
        key = (ref.path, ref.purpose, ref.content_id, ref.range_kind, ref.symbol or "")
        if key in seen:
            return
        seen.add(key)
        refs.append(ref)

    # 1) 强制层：must ∪ ET ∪ C —— 始终磁盘 FULL（purpose=must）
    forced: set[str] = set(plan.must_full) | set(plan.edit_targets) | set(plan.candidate_full)
    for fl in plan.files:
        rel = fl.relpath.replace("\\", "/")
        if fl.level == "NONE":
            continue
        if rel in forced or fl.is_must or fl.is_edit_target or fl.is_candidate:
            if fl.level == "DIGEST":
                # 强制层不允许停在 DIGEST（V12 语义：must 为 FULL）
                pass
            _add(
                Reference(
                    path=rel,
                    purpose="must",
                    ref_kind="content",
                    range_kind="full",
                )
            )

    # 2) 相关非目标 FULL → 按策略
    mode = getattr(cfg, "cr_related_mode", "full") if getattr(cfg, "cr_enabled", False) else "full"
    for fl in plan.files:
        rel = fl.relpath.replace("\\", "/")
        if fl.level != "FULL":
            continue
        if rel in forced or fl.is_must or fl.is_edit_target or fl.is_candidate:
            continue
        if mode == "none":
            continue
        # full / compact：都先登记磁盘全文引用；compact 在 Expand 时替换正文
        raw = disk_files.get(rel)
        cid = ""
        pin = ""
        if store is not None and raw is not None:
            try:
                unit, _ = store.put_raw(
                    raw,
                    kind="source_full",
                    origin={"file_path": rel},
                )
                cid = unit.content_id
                pin = unit.pin_sha256
            except Exception:
                cid, pin = "", ""
        _add(
            Reference(
                path=rel,
                purpose="related",
                ref_kind="content" if cid else "content",
                content_id=cid,
                pin_sha256=pin,
                range_kind="full",
            )
        )
    return refs


def make_related_ref(
    path: str,
    raw: str,
    store: MemoryStore,
    *,
    mode: str,
    instruction: str = "",
) -> tuple[Reference, str, str]:
    """为相关非目标构造 R + 将交付正文写入 store。

    返回 (ref, deliver_body, deliver_kind)。
    compact → 紧凑正文入库；full → 原文入库。
    """
    from .resolver import compact_source

    if mode == "compact":
        body, kind = compact_source(raw, instruction)
    else:
        body, kind = normalize_body(raw), "source_full"
    unit, _ = store.put_raw(body, kind=kind, origin={"file_path": path})
    ref = Reference(
        path=path,
        purpose="related",
        ref_kind="content",
        content_id=unit.content_id,
        pin_sha256=unit.pin_sha256,
        range_kind="full",
    )
    return ref, unit.body_norm, unit.kind
