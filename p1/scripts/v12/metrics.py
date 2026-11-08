"""Token / FETC 账本（method §1.3）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EpisodeTokenLedger:
    """单 episode：含重试的全部实际 API token。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    retry_tokens: int = 0
    steps: int = 0
    success: bool = False
    notes: list[str] = field(default_factory=list)

    def add_request(self, prompt: int, completion: int, *, is_retry: bool = False) -> None:
        self.prompt_tokens += int(prompt or 0)
        self.completion_tokens += int(completion or 0)
        if is_retry:
            self.retry_tokens += int(prompt or 0) + int(completion or 0)

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def tokens_per_attempted(totals: list[int]) -> float:
    """TPAE = sum T(e) / n_episodes。"""
    n = len(totals)
    if n == 0:
        return float("inf")
    return sum(totals) / n


def tokens_per_successful(totals: list[int], successes: list[bool]) -> float:
    """TPSE；成功数 0 → inf（不得记 0）。"""
    assert len(totals) == len(successes)
    ns = sum(1 for s in successes if s)
    if ns == 0:
        return float("inf")
    return sum(totals) / ns


def fe_tc_total(totals: list[int], successes: list[bool]) -> int:
    return sum(t for t, s in zip(totals, successes) if not s)


def fe_tc_mean(totals: list[int], successes: list[bool]):
    """失败 episode 平均 token；0 失败 → None（NA）。"""
    fails = [t for t, s in zip(totals, successes) if not s]
    if not fails:
        return None
    return sum(fails) / len(fails)
