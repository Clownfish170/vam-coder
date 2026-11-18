"""V13E 外部对照臂策略：LLM 摘要压缩（SUMM）与 BM25 历史检索（RETR）。

仅服务论文对比表的**外部方法对照**；生产臂（F / PROJ / SAH）不调用本模块任何函数。

设计要点：
- SUMM：把最近 `recent` 条之外的历史交给同端点压缩器 → 一行摘要替身。
  摘要器的 prompt/completion **全部计入成本**（公平口径）；
  `sanitize_summary` 剔除围栏与 FILE 标记，避免被 `messages_visibility` 的
  提取器（`_ASSIST_FILE_RE` / `_CTX_FILE_RE`）捕获而污染 O′ 证明。
  代价：旧 FILE 块消失 → 阶段 B 可能 force_full 回灌或 INSUFFICIENT —— 这是
  结构破坏型方法的**真实代价，如实测量**。
- RETR：对历史（除 system 外）按 BM25 对本步指令打分，取 top-k，
  **恒保留最后一条**（最新状态），按原时序返回；纯确定性、零依赖。
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable

SUMM_SYSTEM = (
    "你是上下文压缩器。把给定的 agent 历史压缩成简明中文要点，必须保留："
    "已修改的文件名、每步目标、关键符号与常量、未完成事项。"
    "禁止输出代码块、反引号、FILE: 标记、--- FILE --- 标记；只输出要点。"
)

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[㐀-鿿]")
_FENCE_RE = re.compile(r"```+|~~~+")
_MARK_LINE_RE = re.compile(r"^\s*(?:FILE:|---\s*FILE|===\s)", re.M)

SUMMARY_PREFIX = "（历史摘要 · 压缩器生成 · 非文件内容）\n"


def sanitize_summary(text: str, *, max_chars: int = 900) -> str:
    """剔除围栏与 FILE/段落标记，防污染可见性提取；并限长。"""
    if not text:
        return ""
    t = _FENCE_RE.sub("", text)
    t = _MARK_LINE_RE.sub("", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    if len(t) > max_chars:
        t = t[:max_chars] + "…"
    return t


def summarize_history(
    history: list[dict],
    *,
    call_fn: Callable,
    endpoint: str,
    model: str,
    recent: int = 2,
    max_tokens: int = 180,
    timeout: float = 60.0,
    seed: int = 0,
    cap_chars: int = 6000,
) -> tuple[list[dict], int, int]:
    """把最近 `recent` 条之外的历史压成一行摘要。

    返回 (新历史, 摘要器 prompt_tokens, 摘要器 completion_tokens)。
    调用失败或摘要为空 → 原样返回历史（只可能损失本次压缩，不损失安全性）。
    """
    sys_msgs = [m for m in history if m.get("role") == "system"]
    rest = [m for m in history if m.get("role") != "system"]
    if len(rest) <= max(1, recent):
        return history, 0, 0
    old, keep = rest[:-recent], rest[-recent:]
    old_text = "\n\n".join((m.get("content") or "") for m in old).strip()
    if not old_text:
        return history, 0, 0
    old_text = old_text[:cap_chars]
    try:
        cr = call_fn(
            endpoint,
            model,
            [
                {"role": "system", "content": SUMM_SYSTEM},
                {"role": "user", "content": old_text},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
            timeout=timeout,
            seed=seed,
        )
    except Exception:  # noqa: BLE001
        return history, 0, 0
    aux_p = int(getattr(cr, "prompt_tokens", 0) or 0)
    aux_c = int(getattr(cr, "completion_tokens", 0) or 0)
    if getattr(cr, "error", None):
        return history, aux_p, aux_c
    summary = sanitize_summary(getattr(cr, "text", "") or "")
    if not summary:
        return history, aux_p, aux_c
    merged = {"role": "assistant", "content": SUMMARY_PREFIX + summary}
    return sys_msgs + [merged] + keep, aux_p, aux_c


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def bm25_select(
    messages: list[dict], query: str, *, k: int = 3, k1: float = 1.5, b: float = 0.75
) -> tuple[list[dict], int]:
    """BM25 top-k 历史选择：恒保留 system 与最后一条，按原时序返回。

    返回 (新历史, 保留的非 system 消息数)。
    """
    idxs = [i for i, m in enumerate(messages) if m.get("role") != "system"]
    if k <= 0 or len(idxs) <= k:
        return list(messages), len(idxs)
    docs = [_tokens(messages[i].get("content") or "") for i in idxs]
    n_docs = len(docs)
    avgdl = (sum(len(d) for d in docs) / n_docs) or 1.0
    df: Counter = Counter()
    for d in docs:
        df.update(set(d))
    q = set(_tokens(query))
    scored: list[tuple[float, int]] = []
    for pos, m_idx in enumerate(idxs):
        d = docs[pos]
        dl = len(d) or 1
        tf = Counter(d)
        s = 0.0
        for term in q:
            n = tf.get(term, 0)
            if not n:
                continue
            idf = math.log(1.0 + (n_docs - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * (n * (k1 + 1.0)) / (n + k1 * (1.0 - b + b * dl / avgdl))
        scored.append((s, m_idx))
    scored.sort(key=lambda x: (-x[0], x[1]))
    keep = {m_idx for s, m_idx in scored[:k] if s > 0}
    if not keep:  # 无词面命中 → 退化为"最近 k 条"
        keep = {m_idx for _, m_idx in sorted(scored, key=lambda x: x[1])[-k:]}
    keep.add(idxs[-1])  # 恒保留最新状态
    out = [
        m
        for i, m in enumerate(messages)
        if m.get("role") == "system" or i in keep
    ]
    return out, len([i for i in idxs if i in keep])
