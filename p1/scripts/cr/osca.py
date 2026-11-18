"""OSCA：Online Submodular Context Allocation（ICG + 跨步影子价格）。

在单步 ICG 基础上，episode 内维护 λ：
  λ ← λ + α · max(0, used/B − ρ)
used：本 episode 已选 optional FULL 的 token 累计（近似）。
λ 越大 → 后续步 related 越抠；λ 小 → 前期敢给 extract/依赖。

确定性：仅依赖 state 与本步输入，无随机、无模型调用。不改 VSO。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .icg import ICGCandidate, ICGResult, select_optional_full


@dataclass
class OscState:
    lam: float = 0.02
    used_tokens: int = 0
    steps: int = 0
    alpha: float = 0.01
    rho: float = 0.15  # 目标占用比
    history: list[dict] = field(default_factory=list)


def update_lambda(state: OscState, *, budget_tokens: int) -> float:
    """根据累计占用更新影子价格（确定性）。"""
    state.steps += 1
    if budget_tokens <= 0:
        return state.lam
    occupancy = state.used_tokens / max(1, budget_tokens)
    overshoot = max(0.0, occupancy - state.rho)
    state.lam = max(0.005, min(0.5, state.lam + state.alpha * overshoot * 10.0))
    state.history.append(
        {
            "step": state.steps,
            "used": state.used_tokens,
            "occ": round(occupancy, 4),
            "lam": round(state.lam, 4),
        }
    )
    return state.lam


def select_osca(
    candidates: list[ICGCandidate],
    *,
    instruction: str,
    budget_tokens: int,
    state: OscState,
    forced_paths: set[str] | None = None,
) -> ICGResult:
    """用当前 λ 调用 ICG；入选后累加 used_tokens。"""
    update_lambda(state, budget_tokens=budget_tokens)
    # 将 λ 注入增益：通过临时缩放 budget —— 简化：调用 select 并用 state.lam
    # ICG 内部 _marginal_gain 有固定 lam；此处用“剩余预算收紧”近似价格效应
    remaining = max(32, budget_tokens - state.used_tokens)
    # 价格越高 → 预算越紧（等价于更不愿选大文件）
    effective = max(32, int(remaining / (1.0 + 50.0 * state.lam)))
    result = select_optional_full(
        candidates,
        instruction=instruction,
        budget_tokens=effective,
        forced_paths=forced_paths,
    )
    state.used_tokens += result.total_selected_tokens
    return result
