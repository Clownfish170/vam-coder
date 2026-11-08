"""VAM-Coder V1.1：可见性安全省略 + 外部记忆控制器 + 审计/账本。

不修改 P0 / p1_common 冻结语义；仅供 vam_coder_v1.1 路径使用。
"""

from .visibility import VisibilityTracker, content_sha256, visible_file_blocks
from .controller import MemoryController, RetrievePlan
from .assemble import AssembledV11, assemble_vam_v11
from .audit import CostLedger, InjectionAudit
from .metadata import verify_symbol_injection

__all__ = [
    "VisibilityTracker",
    "content_sha256",
    "visible_file_blocks",
    "MemoryController",
    "RetrievePlan",
    "AssembledV11",
    "assemble_vam_v11",
    "CostLedger",
    "InjectionAudit",
    "verify_symbol_injection",
]
