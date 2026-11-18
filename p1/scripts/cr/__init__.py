"""V1.3A_CR：内容寻址记忆（C）+ 符号引用（R）+ 确定性 Resolver。

仅相关非目标承载形式扩展；E/C/must 与 VSO/O′ 语义不变。
"""

from .store import (
    CrStoreError,
    MemoryStore,
    MemoryUnit,
    Slot,
    content_id_of,
    normalize_body,
    pin_sha256,
)
from .resolver import (
    CrResolveError,
    Reference,
    compact_source,
    mem_block,
    resolve_ref,
    slice_body,
)
from .select import select_refs
from .validate import CrCheck, validate_cr

__all__ = [
    "CrStoreError",
    "MemoryStore",
    "MemoryUnit",
    "Slot",
    "content_id_of",
    "normalize_body",
    "pin_sha256",
    "CrResolveError",
    "Reference",
    "compact_source",
    "mem_block",
    "resolve_ref",
    "slice_body",
    "select_refs",
    "CrCheck",
    "validate_cr",
]
