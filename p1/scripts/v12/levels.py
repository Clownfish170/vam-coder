"""任务感知层级选择与 must_full 闭包。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from .config import AblationConfig
from .targets import EditTargetResult
from .adaptive_features import decide_related_level, has_implementation_body

_EDIT_HINTS = re.compile(
    r"(修改|新增|删除|重命名|返回|写死|同步|实现|添加|更换|变成|应为|edit|add|remove|rename|implement|return|change|update|fix)",
    re.I,
)


@dataclass
class FileLevel:
    relpath: str
    level: str  # FULL | DIGEST | NONE
    is_must: bool = False
    is_edit_target: bool = False  # r2.2 E
    is_candidate: bool = False  # r2.2 C
    r_score: int = 0
    reason: str = ""
    content_sha256: str | None = None
    validity: str = "valid"


@dataclass
class ExpandPlan:
    arm: str
    files: list[FileLevel] = field(default_factory=list)
    must_full: set[str] = field(default_factory=set)
    edit_targets: set[str] = field(default_factory=set)  # E
    candidate_full: set[str] = field(default_factory=set)  # C
    excluded: set[str] = field(default_factory=set)
    target_resolution_reason: dict[str, str] = field(default_factory=dict)
    fuzzy_only_hits: set[str] = field(default_factory=set)
    over_kmax: bool = False
    over_budget: bool = False
    insufficient: bool = False
    insufficient_reasons: list[str] = field(default_factory=list)
    required_context_tokens_est: int | None = None
    available_context_tokens: int | None = None
    est_must_full_tokens: int = 0
    est_digest_tokens: int = 0
    est_optional_full_tokens: int = 0
    dropped_optional_digest: list[str] = field(default_factory=list)
    dropped_optional_full: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    closure_depth: int = 2
    # V1.3-M1: per-file adaptive decisions (pre-exec features)
    adaptive_audit: list[dict] = field(default_factory=list)

    def full_paths(self) -> set[str]:
        return {f.relpath for f in self.files if f.level == "FULL"}

    def digest_paths(self) -> set[str]:
        return {f.relpath for f in self.files if f.level == "DIGEST"}

    def all_injected_paths(self) -> set[str]:
        return {f.relpath for f in self.files if f.level in ("FULL", "DIGEST")}

    def audit(self) -> dict:
        return {
            "arm": self.arm,
            "must_full_count": len(self.must_full),
            "k_max": None,
            "over_kmax": self.over_kmax,
            "over_budget": self.over_budget,
            "est_must_full_tokens": self.est_must_full_tokens,
            "est_digest_tokens": self.est_digest_tokens,
            "est_optional_full_tokens": self.est_optional_full_tokens,
            "insufficient": self.insufficient,
            "insufficient_reasons": list(self.insufficient_reasons),
            "required_context_tokens_est": self.required_context_tokens_est,
            "available_context_tokens": self.available_context_tokens,
            "dropped_optional_digest": list(self.dropped_optional_digest),
            "dropped_optional_full": list(self.dropped_optional_full),
            "fuzzy_only_hits": sorted(self.fuzzy_only_hits),
            "edit_targets": sorted(self.edit_targets),
            "candidate_full": sorted(self.candidate_full),
            "excluded": sorted(self.excluded),
            "must_full": sorted(self.must_full),
            "closure_depth": self.closure_depth,
            "target_resolution_reason": dict(self.target_resolution_reason),
            "rules": list(self.rules),
            "adaptive_audit": list(self.adaptive_audit),
        }


def _est_tokens(nbytes: int, cpt: int) -> int:
    return max(1, nbytes // max(1, cpt))


def dependency_closure(
    targets: set[str],
    symbol_to_files: dict[str, list[str]],
    file_deps: dict[str, set[str]],
    *,
    depth: int,
) -> set[str]:
    """dep_{<=d}^{+}(targets) ∪ callers_{<=d}(targets)。

    file_deps: file -> set of provider files it depends on（provider 边）。
    沿 provider 走 depth 层；再收集依赖闭包内节点的 caller 文件（反向 depth）。
    """
    providers: set[str] = set()
    frontier = set(targets)
    for _ in range(max(0, depth)):
        nxt: set[str] = set()
        for f in frontier:
            for p in file_deps.get(f, set()):
                if p not in providers:
                    providers.add(p)
                    nxt.add(p)
        frontier = nxt
    closed = set(targets) | providers

    # callers: files that depend on closed set, within depth
    reverse: dict[str, set[str]] = {}
    for f, deps in file_deps.items():
        for d in deps:
            reverse.setdefault(d, set()).add(f)
    callers: set[str] = set()
    frontier = set(closed)
    for _ in range(max(0, depth)):
        nxt = set()
        for f in frontier:
            for c in reverse.get(f, set()):
                if c not in closed and c not in callers:
                    callers.add(c)
                    nxt.add(c)
        frontier = nxt
    return closed | callers


def relevance_scores(
    files: list[str],
    instruction: str,
    exact_paths: set[str],
    must: set[str],
    entries_by_file: dict[str, list[dict]],
    *,
    task_aware: bool,
) -> dict[str, int]:
    """r(f|τ)；不决定 must。"""
    scores: dict[str, int] = {}
    for rel in files:
        r = 0
        if task_aware:
            if rel in exact_paths:
                r += 1
            if rel in must:
                r += 2
            ents = entries_by_file.get(rel) or []
            if any(e.get("validity") not in (None, "valid") for e in ents):
                r += 1
            base = rel.split("/")[-1]
            stem = base.rsplit(".", 1)[0] if base else ""
            if stem and len(stem) >= 3 and stem in (instruction or ""):
                r += 1
        else:
            # G: 无任务感知过滤；对索引内文件给中性高分以便 full_if_indexed
            r = 1 if rel in entries_by_file or rel in files else 0
        scores[rel] = r
    return scores


def build_plan(
    *,
    arm_cfg: AblationConfig,
    instruction: str,
    workspace_files: list[str],
    workspace_sha: dict[str, str],
    file_sizes: dict[str, int],
    entries_by_file: dict[str, list[dict]],
    targets: EditTargetResult,
    system_history_tokens_est: int = 0,
    source_by_file: dict[str, str] | None = None,
    file_deps: dict[str, set[str]] | None = None,
) -> ExpandPlan:
    cfg = arm_cfg
    files = [str(f).replace("\\", "/") for f in workspace_files]
    plan = ExpandPlan(arm=cfg.arm, closure_depth=cfg.closure_depth)
    plan.edit_targets = set(targets.exact_paths)  # E
    plan.candidate_full = set(getattr(targets, "candidate_full", set()) or set())
    plan.excluded = set(getattr(targets, "excluded", set()) or set())
    plan.target_resolution_reason = dict(
        getattr(targets, "target_resolution_reason", {}) or {}
    )
    plan.fuzzy_only_hits = set(targets.fuzzy_only_hits)
    # E ∩ C = ∅
    plan.candidate_full -= plan.edit_targets
    plan.rules.append(f"E={len(plan.edit_targets)}")
    plan.rules.append(f"C={len(plan.candidate_full)}")

    # must_full：E ∪ risk ∪ dep（E⊆M）；C 不必∈M 但必须∈F
    must = set(plan.edit_targets)
    for rel, ents in entries_by_file.items():
        if any(e.get("validity") not in (None, "valid") for e in ents):
            must.add(rel)

    if cfg.must_full_dep_closure:
        # build file_deps from entries deps
        file_deps: dict[str, set[str]] = {}
        id_to_file: dict[str, str] = {}
        for f, ents in entries_by_file.items():
            for e in ents:
                sid = e.get("symbol_id")
                if sid:
                    id_to_file[sid] = f
        for f, ents in entries_by_file.items():
            deps = set()
            for e in ents:
                for dep in e.get("deps") or []:
                    if dep in id_to_file:
                        deps.add(id_to_file[dep])
                    elif isinstance(dep, str) and dep.endswith(".py"):
                        deps.add(dep.replace("\\", "/"))
            file_deps[f] = deps
        must |= dependency_closure(
            must, {}, file_deps, depth=cfg.closure_depth
        )

    must = {f for f in must if f in set(files)}
    plan.must_full = must
    plan.rules.append(f"must_full_n={len(must)}")

    scores = relevance_scores(
        files,
        instruction,
        targets.exact_paths,
        must,
        entries_by_file,
        task_aware=cfg.task_aware_r,
    )

    # est tokens
    for f in must:
        plan.est_must_full_tokens += _est_tokens(
            file_sizes.get(f, len(workspace_sha.get(f, "")) * 4), cfg.chars_per_token
        )

    # assign levels
    optional_full: list[FileLevel] = []
    digests: list[FileLevel] = []
    for rel in files:
        is_e = rel in plan.edit_targets
        is_c = rel in plan.candidate_full
        # E 与 C 强制 FULL（r2.2）
        if is_e or is_c:
            plan.files.append(
                FileLevel(
                    relpath=rel,
                    level="FULL",
                    is_must=True,  # 注入义务同 must
                    is_edit_target=is_e,
                    is_candidate=is_c,
                    r_score=scores.get(rel, 0),
                    reason="edit_target" if is_e else "candidate_full",
                    content_sha256=workspace_sha.get(rel),
                    validity=_validity(rel, entries_by_file),
                )
            )
            if rel not in must:
                plan.rules.append(f"forced_full_{'E' if is_e else 'C'}:{rel}")
            continue

        if rel in must:
            plan.files.append(
                FileLevel(
                    relpath=rel,
                    level="FULL",
                    is_must=True,
                    r_score=scores.get(rel, 0),
                    reason="must_full",
                    content_sha256=workspace_sha.get(rel),
                    validity=_validity(rel, entries_by_file),
                )
            )
            continue

        r = scores.get(rel, 0)
        policy = cfg.non_target_related if r >= 1 else cfg.non_target_unrelated

        # V1.3-M1 adaptive_a: related non-target Full/Digest from pre-exec features
        if policy == "adaptive_a" and r >= 1:
            src = (source_by_file or {}).get(rel)
            deps_map = file_deps
            if deps_map is None:
                # build from entries deps if possible
                id_to_file: dict[str, str] = {}
                deps_map = {}
                for f, ents in entries_by_file.items():
                    deps_map.setdefault(f, set())
                    for e in ents:
                        sid = e.get("symbol_id")
                        if sid:
                            id_to_file[sid] = f
                for f, ents in entries_by_file.items():
                    for e in ents:
                        for dep in e.get("deps") or []:
                            if dep in id_to_file:
                                deps_map[f].add(id_to_file[dep])
                            elif isinstance(dep, str) and dep.endswith(".py"):
                                deps_map[f].add(dep.replace("\\", "/"))
            feat = decide_related_level(
                relpath=rel,
                source=src,
                instruction=instruction,
                symbols=None,
                edit_targets=set(targets.exact_paths),
                file_deps=deps_map,
                closure_depth=cfg.closure_depth,
            )
            plan.adaptive_audit.append(
                {
                    "relpath": rel,
                    "implementation_body": feat.implementation_body,
                    "instruction_hit": feat.instruction_hit,
                    "dependency_touch": feat.dependency_touch,
                    "level": "FULL" if feat.upgrade_to_full else "DIGEST",
                    "reason": feat.reason,
                    "uncomputable_reason": feat.uncomputable_reason,
                }
            )
            if feat.upgrade_to_full:
                optional_full.append(
                    FileLevel(
                        relpath=rel,
                        level="FULL",
                        is_must=False,
                        r_score=r,
                        reason=feat.reason,
                        content_sha256=workspace_sha.get(rel),
                    )
                )
            else:
                digests.append(
                    FileLevel(
                        relpath=rel,
                        level="DIGEST",
                        is_must=False,
                        r_score=r,
                        reason=feat.reason,
                        content_sha256=workspace_sha.get(rel),
                    )
                )
            continue

        # V1.3-B (v13b)：看齐 F 的“相关→FULL”，仅在有证据时做减法——
        # 无实现体（纯常量/辅助）的相关文件 → NONE；不可计算 → 保守 FULL（不冒险丢内容）。
        if policy == "f_full_no_body_none" and r >= 1:
            src = (source_by_file or {}).get(rel)
            body, body_reason = has_implementation_body(src)
            if body is False:
                plan.files.append(
                    FileLevel(
                        relpath=rel,
                        level="NONE",
                        r_score=r,
                        reason=f"v13b_no_body:{body_reason}",
                        content_sha256=workspace_sha.get(rel),
                    )
                )
            else:
                optional_full.append(
                    FileLevel(
                        relpath=rel,
                        level="FULL",
                        is_must=False,
                        r_score=r,
                        reason=(
                            "v13b_related_full_body"
                            if body
                            else f"v13b_related_full_uncomputable:{body_reason}"
                        ),
                        content_sha256=workspace_sha.get(rel),
                    )
                )
            continue

        if policy == "full_if_indexed":
            if rel in entries_by_file:
                optional_full.append(
                    FileLevel(
                        relpath=rel,
                        level="FULL",
                        is_must=False,
                        r_score=r,
                        reason="g_full_if_indexed",
                        content_sha256=workspace_sha.get(rel),
                    )
                )
            else:
                plan.files.append(
                    FileLevel(relpath=rel, level="NONE", r_score=r, reason="g_not_indexed")
                )
            continue

        if policy == "full":
            optional_full.append(
                FileLevel(
                    relpath=rel,
                    level="FULL",
                    is_must=False,
                    r_score=r,
                    reason="related_full",
                    content_sha256=workspace_sha.get(rel),
                )
            )
        elif policy == "digest":
            digests.append(
                FileLevel(
                    relpath=rel,
                    level="DIGEST",
                    is_must=False,
                    r_score=r,
                    reason="related_digest",
                    content_sha256=workspace_sha.get(rel),
                )
            )
        else:
            plan.files.append(
                FileLevel(relpath=rel, level="NONE", r_score=r, reason="unrelated_none")
            )

    # K_max: optional full only
    if len(must) > cfg.k_max:
        plan.over_kmax = True
        plan.rules.append(f"over_kmax must={len(must)}>K={cfg.k_max}")

    if optional_full:
        # sort by r desc, then path
        optional_full.sort(key=lambda x: (-x.r_score, x.relpath))
        if len(must) + len(optional_full) > cfg.k_max:
            allowed = max(0, cfg.k_max - len(must))
            keep = optional_full[:allowed]
            drop = optional_full[allowed:]
            plan.over_kmax = plan.over_kmax or bool(drop)
            for d in drop:
                plan.dropped_optional_full.append(d.relpath)
                plan.files.append(
                    FileLevel(
                        relpath=d.relpath,
                        level="NONE",
                        r_score=d.r_score,
                        reason="dropped_optional_full_kmax",
                    )
                )
            optional_full = keep
        for fl in optional_full:
            plan.files.append(fl)
            plan.est_optional_full_tokens += _est_tokens(
                file_sizes.get(fl.relpath, 0), cfg.chars_per_token
            )

    # budget: drop optional digests first
    est_after = plan.est_must_full_tokens + plan.est_optional_full_tokens
    digest_items = list(digests)
    if est_after > cfg.budget_tokens:
        plan.over_budget = True
    for d in digest_items:
        est_d = _est_tokens(file_sizes.get(d.relpath, 0), cfg.chars_per_token)
        if plan.est_must_full_tokens + plan.est_optional_full_tokens + plan.est_digest_tokens + est_d > cfg.budget_tokens:
            plan.over_budget = True
            plan.dropped_optional_digest.append(d.relpath)
            plan.files.append(
                FileLevel(
                    relpath=d.relpath,
                    level="NONE",
                    r_score=d.r_score,
                    reason="dropped_optional_digest_budget",
                )
            )
        else:
            plan.files.append(d)
            plan.est_digest_tokens += est_d

    # context window safety
    required = (
        system_history_tokens_est
        + plan.est_must_full_tokens
        + plan.est_digest_tokens
        + plan.est_optional_full_tokens
    )
    plan.required_context_tokens_est = required
    plan.available_context_tokens = cfg.context_window
    if required > cfg.context_window:
        # 不截断 must；标记 INSUFFICIENT
        plan.insufficient = True
        plan.insufficient_reasons.append("REQUIRED_CONTEXT_EXCEEDS_LIMIT")
        plan.rules.append("REQUIRED_CONTEXT_EXCEEDS_LIMIT")

    plan.files.sort(key=lambda f: f.relpath)
    # attach k_max to audit via closure_depth field already
    return plan


def _validity(rel: str, entries_by_file: dict[str, list[dict]]) -> str:
    ents = entries_by_file.get(rel) or []
    for e in ents:
        v = e.get("validity")
        if v and v != "valid":
            return v
    return "valid"
