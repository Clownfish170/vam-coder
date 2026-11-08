"""编辑目标精确解析（r2.2）：正向意图 + 否定作用域；E / Excluded / CandidateFull。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_WORD_BOUNDARY_FMT = r"(?<![A-Za-z0-9_]){name}(?![A-Za-z0-9_])"

_NEG_VERBS = re.compile(
    r"(不要修改|不要动|禁止改动|保持不变|勿改|禁止修改|do not modify|don't change|dont change|leave unchanged)",
    re.I,
)
_POS_VERBS = re.compile(
    r"(修改|新增|删除|重命名|返回|写死|同步|实现|添加|更换|变成|应为|edit|add|remove|rename|implement|return|change|update|fix)",
    re.I,
)
_CLAUSE_SPLIT = re.compile(r"[。；;\n]")


def _boundary_re(name: str) -> re.Pattern:
    return re.compile(_WORD_BOUNDARY_FMT.format(name=re.escape(name)))


def _norm(p: str) -> str:
    return str(p).replace("\\", "/").strip()


@dataclass
class EditTargetResult:
    exact_paths: set[str] = field(default_factory=set)  # E
    exact_symbols: set[str] = field(default_factory=set)
    excluded: set[str] = field(default_factory=set)
    candidate_full: set[str] = field(default_factory=set)
    fuzzy_only_hits: set[str] = field(default_factory=set)
    ambiguous_symbols: set[str] = field(default_factory=set)
    target_resolution_reason: dict[str, str] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    @property
    def edit_targets(self) -> set[str]:
        return set(self.exact_paths)


def parse_edit_targets(
    instruction: str,
    workspace_files: list[str],
    symbol_to_files: dict[str, list[str]] | None = None,
) -> EditTargetResult:
    instr = instruction or ""
    files = [_norm(f) for f in workspace_files]
    result = EditTargetResult()
    symbol_to_files = symbol_to_files or {}

    clauses = [c.strip() for c in _CLAUSE_SPLIT.split(instr) if c and c.strip()]
    if not clauses:
        clauses = [instr.strip()] if instr.strip() else []

    positive: set[str] = set()
    negative: set[str] = set()

    for clause in clauses:
        has_neg = bool(_NEG_VERBS.search(clause))
        has_pos = bool(_POS_VERBS.search(clause))
        # 注意：「不要修改」同时含「修改」→ 否定优先
        if has_neg and not has_pos:
            kind = "neg"
        elif has_neg and has_pos:
            # 否定短语内的「修改」不算正向；若另有独立正向动词则 conflict
            stripped = _NEG_VERBS.sub("", clause)
            has_pos_other = bool(_POS_VERBS.search(stripped))
            if has_pos_other:
                kind = "conflict"
            else:
                kind = "neg"
        elif has_pos:
            kind = "pos"
        else:
            kind = "neutral"

        for rel in files:
            base = rel.split("/")[-1]
            if not base or not _boundary_re(base).search(clause):
                continue
            if kind == "neg":
                negative.add(rel)
            elif kind == "pos":
                positive.add(rel)
            elif kind == "conflict":
                # 同句正负 → 保守正向
                positive.add(rel)
                result.target_resolution_reason[rel] = "conflict_positive_negative"

        if kind == "pos":
            for sym, paths in symbol_to_files.items():
                if not sym or len(sym) < 2:
                    continue
                if not _boundary_re(sym).search(clause):
                    continue
                result.exact_symbols.add(sym)
                if len(paths) == 1:
                    positive.add(_norm(paths[0]))
                    result.target_resolution_reason.setdefault(
                        _norm(paths[0]), "positive_symbol_exact"
                    )
                elif len(paths) > 1:
                    result.ambiguous_symbols.add(sym)
                    for p in paths:
                        positive.add(_norm(p))
                    result.reasons.append(f"symbol_ambiguous:{sym}:{paths}")

    # 否定且未被正向覆盖 → excluded
    for rel in negative:
        if rel in positive:
            result.target_resolution_reason.setdefault(rel, "conflict_positive_negative")
            continue
        result.excluded.add(rel)
        result.reasons.append(f"excluded_negative:{rel}")
        result.target_resolution_reason[rel] = "negative_clause"

    for rel in positive:
        result.exact_paths.add(rel)
        result.target_resolution_reason.setdefault(rel, "positive_edit_clause")
        result.reasons.append(f"path_exact:{rel}")

    # 模糊仅审计
    for rel in files:
        stem = rel.split("/")[-1].rsplit(".", 1)[0] if rel else ""
        if (
            stem
            and len(stem) >= 3
            and stem in instr
            and rel not in result.exact_paths
            and rel not in result.excluded
            and not _boundary_re(stem).search(instr)
        ):
            result.fuzzy_only_hits.add(rel)

    # CandidateFull：有编辑动词但无正向路径；范围限弱关联（≤3）
    if _POS_VERBS.search(instr) and not positive:
        weak = [
            rel
            for rel in files
            if rel not in result.excluded
            and (
                rel.split("/")[-1].split(".")[0] in instr
                or len(files) == 1
            )
        ]
        if 0 < len(weak) <= 3:
            for rel in weak:
                result.candidate_full.add(rel)
                result.target_resolution_reason[rel] = "ambiguous_scope_candidate_full"
                result.reasons.append(f"candidate_full:{rel}")

    result.candidate_full -= result.exact_paths
    return result


def fuzzy_hits(result: EditTargetResult) -> set[str]:
    return set(result.fuzzy_only_hits)
