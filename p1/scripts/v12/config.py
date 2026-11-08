"""V1.2 消融配置（E/F/G/H）+ r2.2 编辑安全开关。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields

ARCH_VERSION = "v1.2-r2.2"


@dataclass(frozen=True)
class AblationConfig:
    arm: str  # E | F | G | H
    exact_targets: bool = True
    must_full_dep_closure: bool = True
    o_prime: bool = True
    # r2.2：编辑目标/候选禁 O′（正式默认 true）
    edit_target_oprime_forbid: bool = True
    candidate_full_oprime_forbid: bool = True
    # 非目标策略：digest | full | none | full_if_indexed | adaptive_a | f_full_no_body_none
    non_target_related: str = "digest"
    non_target_unrelated: str = "none"
    task_aware_r: bool = True
    k_max: int = 8
    closure_depth: int = 2
    budget_tokens: int = 4096
    context_window: int = 8192
    chars_per_token: int = 4
    max_files: int = 32

    def to_dict(self) -> dict:
        return asdict(self)

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_ARMS: dict[str, dict] = {
    "E": {
        "non_target_related": "digest",
        "non_target_unrelated": "none",
        "task_aware_r": True,
    },
    "F": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
    },
    "G": {
        "non_target_related": "full_if_indexed",
        "non_target_unrelated": "full_if_indexed",
        "task_aware_r": False,
    },
    "H": {
        "non_target_related": "none",
        "non_target_unrelated": "none",
        "task_aware_r": True,
    },
    # V1.3-M1: opt-in adaptive related policy (does not change E/F/G/H)
    "V13A": {
        "non_target_related": "adaptive_a",
        "non_target_unrelated": "none",
        "task_aware_r": True,
    },
    # V1.3-B: F 默认（相关→FULL），无实现体→NONE；不可计算→保守 FULL
    "V13B": {
        "non_target_related": "f_full_no_body_none",
        "non_target_unrelated": "none",
        "task_aware_r": True,
    },
}


def load_arm(arm: str, **overrides) -> AblationConfig:
    arm = arm.upper()
    if arm not in _ARMS:
        raise ValueError(f"unknown arm: {arm}")
    base = {
        "arm": arm,
        "exact_targets": True,
        "must_full_dep_closure": True,
        "o_prime": True,
        "edit_target_oprime_forbid": True,
        "candidate_full_oprime_forbid": True,
        "k_max": 8,
        "closure_depth": 2,
        "budget_tokens": 4096,
        "context_window": 8192,
        "chars_per_token": 4,
        "max_files": 32,
        **_ARMS[arm],
    }
    base.update(overrides)
    return AblationConfig(**base)


def config_diff(a: AblationConfig, b: AblationConfig) -> set[str]:
    keys = {f.name for f in fields(AblationConfig)} - {"arm"}
    return {k for k in keys if getattr(a, k) != getattr(b, k)}
