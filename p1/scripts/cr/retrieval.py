"""确定性倒排检索：指令 → 候选文件（无 embedding、无模型调用）。"""

from __future__ import annotations

import re
from collections import defaultdict

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}|[一-鿿]{2,}")

# 停用/弱词（不参与候选打分）
_STOP = {
    "请", "修改", "新增", "删除", "返回", "当前", "不要", "中", "的",
    "the", "and", "for", "with", "that", "this", "from", "into",
}


def tokenize(text: str) -> list[str]:
    out = []
    for m in _TOKEN_RE.finditer(text or ""):
        t = m.group(0).lower()
        if t in _STOP or len(t) < 2:
            continue
        out.append(t)
    return out


def build_file_index(
    files: dict[str, str],
    *,
    max_symbols_per_file: int = 32,
) -> dict[str, set[str]]:
    """token → set(file_path)。token 含：路径 stem、文件名、符号名（粗拆）。"""
    index: dict[str, set[str]] = defaultdict(set)
    for path, src in files.items():
        base = path.split("/")[-1]
        stem = base.rsplit(".", 1)[0] if "." in base else base
        for tok in (base.lower(), stem.lower(), path.lower()):
            index[tok].add(path)
        # 符号：def/class/赋值左侧名（正则，确定性）
        n = 0
        for m in re.finditer(
            r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)|^([A-Za-z_][A-Za-z0-9_]*)\s*=",
            src or "",
            re.M,
        ):
            name = (m.group(1) or m.group(2) or "").lower()
            if len(name) < 3 or name in _STOP:
                continue
            index[name].add(path)
            n += 1
            if n >= max_symbols_per_file:
                break
    return index


def retrieve_candidates(
    instruction: str,
    index: dict[str, set[str]],
    *,
    universe: set[str] | None = None,
    max_hits: int = 16,
) -> dict[str, int]:
    """指令 token 命中计数 → {path: score}。universe 限制在 workspace 内。"""
    scores: dict[str, int] = defaultdict(int)
    for tok in set(tokenize(instruction)):
        for path in index.get(tok, ()):
            if universe is not None and path not in universe:
                continue
            scores[path] += 1
    # 确定性：分数降序，path 字典序
    items = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(items[:max_hits])
