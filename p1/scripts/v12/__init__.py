"""VAM-Coder V1.2 (v1.2-r2.1)：任务感知上下文装配。

不修改 V1.0/V1.1 冻结行为；仅供 vam_coder_v1.2 与消融臂使用。
"""

from .config import ARCH_VERSION, AblationConfig, config_diff, load_arm
from .targets import EditTargetResult, parse_edit_targets, fuzzy_hits
from .levels import ExpandPlan, FileLevel, build_plan
from .assemble import AssembledV12, assemble_v12
from .metrics import EpisodeTokenLedger, fe_tc_total, fe_tc_mean, tokens_per_attempted, tokens_per_successful
from .audit import V12Audit

__all__ = [
    "ARCH_VERSION",
    "AblationConfig",
    "config_diff",
    "load_arm",
    "EditTargetResult",
    "parse_edit_targets",
    "fuzzy_hits",
    "ExpandPlan",
    "FileLevel",
    "build_plan",
    "AssembledV12",
    "assemble_v12",
    "EpisodeTokenLedger",
    "fe_tc_total",
    "fe_tc_mean",
    "tokens_per_attempted",
    "tokens_per_successful",
    "V12Audit",
]
