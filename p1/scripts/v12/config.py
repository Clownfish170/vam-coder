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
    # V1.3A_CR：相关非目标承载扩展（默认关闭 = 行为与冻结 V12-F 一致）
    cr_enabled: bool = False
    cr_related_mode: str = "full"  # full | compact | none
    # V13A_testpart：ICG 子模选择（相关可选 FULL 子集；不改 VSO）
    icg_enabled: bool = False
    icg_budget_tokens: int = 512
    # V13B 特别版：跨步影子价格 + 倒排检索
    osca_enabled: bool = False
    retrieval_enabled: bool = False
    # V13D 预览：验证锚定慢层（跨集蒸馏）
    slow_enabled: bool = False
    # V13E·SAH：状态锚定历史（默认关闭 → 既有臂配置摘要逐字节不变）
    #   sah_project = S1 历史状态投影（逐路径 last-write-wins，对 O′ 等价）
    #   sah_ledger  = S2 义务账本（窄口径 + 只留未结，TASK 与 CONTEXT 之间）
    #   sah_project_mode：
    #     "last"       = 每文件只留最后一版（省得最多）
    #     "first_last" = 保留首版+末版、折叠中间版（保留编辑轨迹端点；
    #                    1.5B 筛选中 M04a 分叉显示仅留末版会改变贪心轨迹）
    sah_project: bool = False
    sah_ledger: bool = False
    sah_project_mode: str = "last"
    # V13E 外部对照臂（论文对比表；生产臂默认关闭）
    #   hist_summary  = SUMM：LLM 摘要压缩（摘要器 token 全计）
    #   hist_retrieve = RETR：BM25 top-k 历史检索
    #   TRUNC 滑窗截断由 runner 的 args.max_history_chars 控制（按臂覆盖预算）
    hist_summary: bool = False
    hist_summary_recent: int = 2
    hist_retrieve: bool = False
    hist_retrieve_k: int = 3

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
    # V1.3A_CR：相关非目标 → 紧凑 C + MEM 展开（E/C/must 仍 FILE 全量）
    "V13ACR": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "cr_enabled": True,
        "cr_related_mode": "compact",
    },
    # V13A_SID：单 ID 对照——同样紧凑正文，但 cr 关闭外部 Slot/依赖层（装配仍走 MEM 形态）
    "V13ASID": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "cr_enabled": True,
        "cr_related_mode": "compact",
    },
    # 基线：无 VAM 记忆（每步全仓倾倒）；runner 走 assemble_memory_off
    "MEMORYOFF": {
        "non_target_related": "none",
        "non_target_unrelated": "none",
        "task_aware_r": False,
        "cr_enabled": False,
        "o_prime": False,
    },
    # V13A_testpart：ICG — 相关非目标按信息覆盖贪心选取 FULL 子集（其余 NONE）
    "V13AICG": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "icg_enabled": True,
        "icg_budget_tokens": 512,
        "cr_enabled": False,
    },
    # V13B = V13A 迭代（testpart 通过）：
    #   继承 V13A：外部 C 库（cr_enabled）+ fail-closed 校验路径
    #   新增 ICG：相关可选 FULL 子集选取（替换 V13A 的 related 一律跳过）
    #   cr_related_mode=full：ICG 落选已在 plan 层降为 NONE；
    #   入选保持 FULL 走 FILE，assemble 不再 blanket-skip
    # 架构 ID = vam_coder_v1.3B_ICG（勿与已废弃 no-body 臂 V13B 混淆）
    "V13BICG": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "icg_enabled": True,
        "icg_budget_tokens": 512,
        "cr_enabled": True,
        "cr_related_mode": "full",
    },
    # V13B testpart 命名别名（与 V13BICG 同配置，便于三臂报告对齐）
    "V13BTESTPART": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "icg_enabled": True,
        "icg_budget_tokens": 512,
        "cr_enabled": True,
        "cr_related_mode": "full",
    },
    # V13B 特别版：ICG + OSCA 跨步价格 + 倒排检索 + C 库
    # 有收益 → 迭代 V13C
    "V13BSP": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "icg_enabled": True,
        "icg_budget_tokens": 512,
        "cr_enabled": True,
        "cr_related_mode": "full",
        "osca_enabled": True,
        "retrieval_enabled": True,
    },
    # V13D 预览 = V13C(ICG) + 验证锚定慢层（跨集蒸馏）
    "V13DVAD": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "icg_enabled": True,
        "icg_budget_tokens": 512,
        "cr_enabled": True,
        "cr_related_mode": "full",
        "slow_enabled": True,
    },
    # V13E·SAH：状态锚定历史（设计稿 p1/docs/v13e_sah_design.md）
    # 基座 F + 仅 S1 投影（消融）
    "V13EPROJ": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "sah_project": True,
    },
    # 基座 F + S1 投影 + S2 账本（主臂）
    "V13ESAH": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "sah_project": True,
        "sah_ledger": True,
    },
    # 基座 ICG(v13c) + S1 + S2（全栈臂）
    "V13ICGSAH": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "icg_enabled": True,
        "icg_budget_tokens": 512,
        "cr_enabled": True,
        "cr_related_mode": "full",
        "sah_project": True,
        "sah_ledger": True,
    },
    # ---- V13E 外部对照（论文对比表，与 F 同配置仅历史策略不同）----
    # A 滑动窗口截断（SWE-agent/OpenHands 类默认）：预算由 args.max_history_chars 按臂覆盖
    "TRUNC": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
    },
    # B LLM 摘要压缩（LLMLingua / MemGPT 系）：摘要器成本全计
    "SUMM": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "hist_summary": True,
        "hist_summary_recent": 2,
    },
    # C BM25 历史检索（RAG / Generative Agents 系）：top-k + 恒留最新
    "RETR": {
        "non_target_related": "full",
        "non_target_unrelated": "none",
        "task_aware_r": True,
        "hist_retrieve": True,
        "hist_retrieve_k": 3,
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
