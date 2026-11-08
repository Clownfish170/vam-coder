"""外部记忆控制器（EMC）：决定本步是否检索、注入哪些 symbol/file。

规则 R0–R4 见 v1.1_architecture_design.md §3.1。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_EDIT_HINTS = re.compile(
    r"(修改|新增|删除|重命名|返回|写死|同步|实现|添加|更换|变成|应为|新增函数|"
    r"edit|add|remove|rename|implement|return|change|update|fix)",
    re.I,
)


@dataclass
class FilePlan:
    relpath: str
    action: str  # EXPAND | REUSE_KV | DROP
    symbol_ids: list[str] = field(default_factory=list)
    validity: str = "valid"
    content_sha256: str | None = None
    reason: str = ""


@dataclass
class RetrievePlan:
    need: bool
    mode: str  # full_repo | indexed_files | none
    files: list[FilePlan] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)
    estimated_inject_tokens: int = 0
    insufficient: bool = False
    notes: list[str] = field(default_factory=list)

    def expand_paths(self) -> set[str]:
        return {f.relpath for f in self.files if f.action == "EXPAND"}

    def all_paths(self) -> set[str]:
        return {f.relpath for f in self.files}


@dataclass
class MemoryController:
    """轻量可解释控制器；不调用模型。"""

    max_files: int = 32
    min_visible_files: int = 2

    def decide(
        self,
        *,
        instruction: str,
        workspace_files: list[str],
        entries_by_file: dict[str, list[dict]],
        visibility_paths: set[str],
        dependency_closure_files: set[str],
        workspace_sha: dict[str, str] | None = None,
    ) -> RetrievePlan:
        rules: list[str] = []
        files_meta = list(workspace_files)
        sha_map = dict(workspace_sha or {})

        # R0 空索引 → 全量
        if not entries_by_file:
            rules.append("R0_empty_index_full_repo")
            plans = [
                FilePlan(relpath=rel, action="EXPAND", reason="R0_full_repo")
                for rel in files_meta[: self.max_files]
            ]
            return RetrievePlan(
                need=True,
                mode="full_repo",
                files=plans,
                rules_fired=rules,
                estimated_inject_tokens=sum(40 for _ in plans),
            )

        hint = bool(_EDIT_HINTS.search(instruction or ""))
        touched = set(dependency_closure_files)
        # 任务相关文件：指令中出现的路径名
        for rel in files_meta:
            base = rel.split("/")[-1]
            if base and base in (instruction or ""):
                touched.add(rel)

        # R2 无编辑意图且无依赖 → 不检索
        if not hint and not touched:
            rules.append("R2_no_need")
            return RetrievePlan(need=False, mode="none", rules_fired=rules)

        rules.append("R1_need_related_files")
        # 必须可见：依赖闭包 + 指令命中 + stale/unverified（强制 EXPAND）
        force_visible: set[str] = set()
        for rel, ents in entries_by_file.items():
            for e in ents:
                if e.get("validity") in ("stale", "unverified"):
                    force_visible.add(rel)
        must_expand = set(touched) | force_visible

        selected = sorted((touched | force_visible | set(entries_by_file)) & set(files_meta))
        if not selected:
            selected = sorted(files_meta)[: self.max_files]
            rules.append("R0_fallback_select_all_indexed")

        plans: list[FilePlan] = []
        for rel in selected[: self.max_files]:
            ents = entries_by_file.get(rel, [])
            file_sha = sha_map.get(rel)
            if not ents:
                plans.append(
                    FilePlan(
                        relpath=rel,
                        action="EXPAND",
                        content_sha256=file_sha,
                        reason="no_symbols_on_disk_index",
                    )
                )
                continue
            nonvalid = [e for e in ents if e.get("validity") != "valid"]
            if nonvalid or rel in must_expand:
                reason = (
                    "R4_nonvalid_forces_expand"
                    if nonvalid
                    else "R1_edit_or_dependency_target"
                )
                plans.append(
                    FilePlan(
                        relpath=rel,
                        action="EXPAND",
                        symbol_ids=[e["symbol_id"] for e in ents],
                        validity=(nonvalid[0].get("validity", "valid") if nonvalid else "valid"),
                        content_sha256=file_sha,
                        reason=reason,
                    )
                )
            else:
                plans.append(
                    FilePlan(
                        relpath=rel,
                        action="REUSE_KV",
                        symbol_ids=[e["symbol_id"] for e in ents],
                        validity="valid",
                        content_sha256=file_sha,
                        reason="candidate_reuse_subject_to_O_prime",
                    )
                )

        # R3：编辑相关步至少保证 min_visible 个 EXPAND；不足则把候选省略升为 EXPAND
        if hint or touched:
            expand_n = sum(1 for p in plans if p.action == "EXPAND")
            if expand_n < self.min_visible_files:
                for p in plans:
                    if p.action == "REUSE_KV" and expand_n < self.min_visible_files:
                        p.action = "EXPAND"
                        p.reason = "R3_min_visible_files"
                        expand_n += 1
                rules.append("R3_min_visible_files_forced_expand")

        est = sum(50 if p.action == "EXPAND" else 8 for p in plans)
        return RetrievePlan(
            need=True,
            mode="indexed_files",
            files=plans,
            rules_fired=rules,
            estimated_inject_tokens=est,
        )

    def apply_visibility_veto(
        self, plan: RetrievePlan, tracker, workspace_sha: dict[str, str]
    ) -> RetrievePlan:
        """R3：无可见性证明的 REUSE_KV → EXPAND。"""
        vetoed = 0
        for p in plan.files:
            if p.action != "REUSE_KV":
                continue
            sha = p.content_sha256 or workspace_sha.get(p.relpath)
            if not sha:
                p.action = "EXPAND"
                p.reason = "R3_no_sha"
                vetoed += 1
                continue
            if not tracker.has_visible(p.relpath, sha):
                p.action = "EXPAND"
                p.reason = "R3_visibility_veto"
                vetoed += 1
        if vetoed:
            plan.rules_fired.append(f"R3_veto_{vetoed}")
        return plan
