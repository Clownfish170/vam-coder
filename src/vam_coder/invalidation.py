"""失效管理器：源码变更检测、版本校验、依赖闭包失效、tombstone。

规则（对齐报告 §4.5，closure_depth 默认 2）：
1. 解析哈希 == source_hash（上次观察）→ 完全不变，零状态写入（幂等）。
   仅当解析出的 deps 漂移时刷新依赖边（不动版本/validity）。
2. 解析哈希 != source_hash → 观察到变化：source_hash 更新、version+1；
   若新哈希 == content_hash（记忆依据）→ 源码回退，恢复 valid；
   否则 validity=stale（旧记忆失效，禁止 REUSE_KV）。
   注：content_hash 不更新——它是“记忆建立时的依据”，stale 即由
   content_hash != source_hash 驱动，可被回退或 verify 恢复。
3. 符号在库中但源码中消失（删除/重命名）→ tombstoned（不再是有效对象）。
4. 集合（2∪3）沿依赖边反向传播 ≤closure_depth 层 → dependents 置
   unverified（已是 stale/tombstoned 的保持原状态；已 unverified 幂等跳过）。
5. unverified 恢复：显式 verify() 重解析该符号并重哈希，匹配记忆依据
   → valid；失配 → stale；符号消失 → tombstoned。
   sync() 不自动治愈 unverified（保守：依赖语义可能已变，需显式校验）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import AppConfig
from .logging_util import JsonlLogger
from .models import MemoryEntry, SymbolDraft, Validity
from .parser import ParseResult, parse_repo, parse_source
from .store import StaticStore


@dataclass
class SyncOutcome:
    repo_id: str
    repo_version_before: int
    repo_version_after: int
    inserted: list[str] = field(default_factory=list)
    content_changed: list[str] = field(default_factory=list)
    reverted: list[str] = field(default_factory=list)
    tombstoned: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    unchanged_count: int = 0
    deps_refreshed: list[str] = field(default_factory=list)
    skipped_files: list[dict] = field(default_factory=list)
    parse_warnings: list[dict] = field(default_factory=list)

    @property
    def mutated(self) -> bool:
        return bool(
            self.inserted or self.content_changed or self.reverted
            or self.tombstoned
        )


def dependency_closure(
    seeds: set[str],
    depth: int,
    direct_dependents,
) -> dict[str, int]:
    """反向依赖闭包：返回 {symbol_id: 层深(1..depth)}，不含 seeds 本身。"""
    visited: set[str] = set(seeds)
    frontier = set(seeds)
    result: dict[str, int] = {}
    for d in range(1, depth + 1):
        nxt: set[str] = set()
        for s in sorted(frontier):
            for p in direct_dependents(s):
                if p not in visited:
                    visited.add(p)
                    nxt.add(p)
                    result[p] = d
        if not nxt:
            break
        frontier = nxt
    return result


def summary_stub(source_text: str, qualified_name: str) -> str:
    """P0 摘要：确定性抽取式（docstring 优先），非模型生成 → 模拟功能。"""
    lines = source_text.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            body = stripped.strip("\"'").strip()
            if body:
                return f"{qualified_name}: {body[:80]}"
    non_empty = [ln for ln in lines if ln.strip()]
    first = non_empty[0].strip() if non_empty else ""
    return f"{qualified_name}: {len(non_empty)} lines; {first[:80]}"


def kv_ptr_stub(content_hash_hex: str) -> str:
    """模拟 KV 分片指针（本阶段不落真实张量）→ 模拟功能。"""
    return f"sim://kv/py-model/{content_hash_hex[:16]}"


class InvalidationManager:
    def __init__(
        self,
        store: StaticStore,
        config: AppConfig,
        logger: JsonlLogger | None = None,
    ):
        self.store = store
        self.config = config
        self.logger = logger or JsonlLogger(None)

    # ---------- 主流程 ----------
    def sync(self, repo_root: str | Path, repo_id: str) -> SyncOutcome:
        repo_root = Path(repo_root)
        parsed = parse_repo(repo_root, repo_id, self.config)
        return self.sync_parsed(repo_root, repo_id, parsed)

    def sync_parsed(
        self, repo_root: Path, repo_id: str, parsed: ParseResult
    ) -> SyncOutcome:
        cfg = self.config
        before = self.store.get_repo_version(repo_id)
        outcome = SyncOutcome(
            repo_id=repo_id,
            repo_version_before=before,
            repo_version_after=before,
            skipped_files=list(parsed.skipped_files),
            parse_warnings=list(parsed.parse_warnings),
        )
        existing = self.store.list_symbols(repo_id, include_tombstoned=True)
        present = {d.symbol_id for d in parsed.symbols}

        # ---- 阶段 A：分类（不写库）----
        inserts: list[tuple[SymbolDraft, int | None]] = []
        changes: list[tuple[SymbolDraft, MemoryEntry]] = []
        reverts: list[tuple[SymbolDraft, MemoryEntry]] = []
        deps_refresh: list[tuple[str, list[str]]] = []
        for draft in sorted(parsed.symbols, key=lambda d: d.symbol_id):
            cur = existing.get(draft.symbol_id)
            if cur is None:
                inserts.append((draft, None))
            elif cur.validity == Validity.TOMBSTONED.value:
                # 已 tombstone 的符号重新出现 → 复活，版本接续单调
                inserts.append((draft, cur.version))
            elif draft.content_hash == cur.source_hash:
                if sorted(draft.deps) != sorted(cur.deps):
                    # 延迟到闭包之后刷新：过早清边会切断 tombstone 的传播路径
                    deps_refresh.append((draft.symbol_id, sorted(draft.deps)))
                outcome.unchanged_count += 1
            elif draft.content_hash == cur.content_hash:
                reverts.append((draft, cur))
            else:
                changes.append((draft, cur))

        tombstones = [
            sid
            for sid in sorted(existing)
            if existing[sid].validity != Validity.TOMBSTONED.value
            and sid not in present
        ]

        mutated = bool(inserts or changes or reverts or tombstones)
        after = self.store.bump_repo_version(repo_id) if mutated else before

        def symbol_text(draft: SymbolDraft) -> str:
            src = (repo_root / draft.file_path).read_bytes()
            return src[draft.start_byte : draft.end_byte].decode(
                "utf-8", errors="replace"
            )

        # ---- 阶段 B：统一应用（repo_version = after）----
        for draft, prev_version in inserts:
            text = symbol_text(draft)
            version = 1 if prev_version is None else prev_version + 1
            entry = MemoryEntry(
                symbol_id=draft.symbol_id,
                repo_id=repo_id,
                file_path=draft.file_path,
                qualified_name=draft.qualified_name,
                kind=draft.kind,
                content_hash=draft.content_hash,
                source_hash=draft.content_hash,
                version=version,
                deps=sorted(draft.deps),
                summary=summary_stub(text, draft.qualified_name)
                if cfg.simulate_summary else None,
                validity=Validity.VALID.value,
                kv_ptr=kv_ptr_stub(draft.content_hash) if cfg.simulate_kv else None,
                provenance={
                    "task_id": "p0-sync",
                    "repo_version": after,
                    "outcome": "indexed",
                },
                size_bytes=draft.size_bytes,
                start_line=draft.start_line,
                end_line=draft.end_line,
                last_seen_repo_version=after,
                updated_at=_now_iso(),
            )
            self.store.insert_symbol(entry)
            outcome.inserted.append(draft.symbol_id)
            self.logger.emit(
                "insert", repo_id=repo_id, symbol_id=draft.symbol_id,
                version=version, content_hash=draft.content_hash,
                deps=entry.deps, repo_version=after,
                reason="new symbol indexed" if prev_version is None
                else "tombstoned symbol reappeared → resurrected as valid",
            )

        for draft, cur in changes:
            new_version = cur.version + 1
            # summary/kv_ptr 是“记忆依据(content_hash)”的产物：依据未变则保留；
            # 只有 source_hash/version/validity/span/size 跟随当前源码更新
            self.store.apply_source_change(
                draft.symbol_id,
                source_hash=draft.content_hash,
                version=new_version,
                validity=Validity.STALE.value,
                size_bytes=draft.size_bytes,
                start_line=draft.start_line,
                end_line=draft.end_line,
                repo_version=after,
                deps=draft.deps,
                summary=cur.summary,
                kv_ptr=cur.kv_ptr,
            )
            outcome.content_changed.append(draft.symbol_id)
            self.logger.emit(
                "content_stale", repo_id=repo_id, symbol_id=draft.symbol_id,
                reason="observed source_hash differs from memory basis "
                       "content_hash → stale (REUSE_KV forbidden)",
                content_hash=cur.content_hash, new_source_hash=draft.content_hash,
                version=new_version, repo_version=after,
            )

        for draft, cur in reverts:
            self.store.apply_source_change(
                draft.symbol_id,
                source_hash=draft.content_hash,
                version=cur.version + 1,
                validity=Validity.VALID.value,
                size_bytes=draft.size_bytes,
                start_line=draft.start_line,
                end_line=draft.end_line,
                repo_version=after,
                deps=draft.deps,
                summary=cur.summary,
                kv_ptr=cur.kv_ptr,
            )
            outcome.reverted.append(draft.symbol_id)
            self.logger.emit(
                "content_reverted", repo_id=repo_id, symbol_id=draft.symbol_id,
                reason="source reverted to memory basis content_hash → valid",
                version=cur.version + 1, repo_version=after,
            )

        for sid in tombstones:
            self.store.tombstone(sid, after)
            outcome.tombstoned.append(sid)
            self.logger.emit(
                "tombstone", repo_id=repo_id, symbol_id=sid,
                reason="symbol absent after re-parse (deleted or renamed) "
                       "→ no longer a valid object",
                repo_version=after,
            )

        # ---- 阶段 C：依赖闭包传播 → unverified ----
        seeds = set(outcome.content_changed) | set(outcome.tombstoned)
        if seeds:
            closure = dependency_closure(
                seeds, cfg.closure_depth, self.store.direct_dependents
            )
            for sid in sorted(closure):
                entry = self.store.get(sid)
                if entry is None:
                    continue
                if entry.validity in (
                    Validity.STALE.value, Validity.TOMBSTONED.value
                ):
                    continue  # 更严重状态优先
                if entry.validity == Validity.UNVERIFIED.value:
                    continue  # 幂等
                self.store.set_validity(sid, Validity.UNVERIFIED.value)
                outcome.unverified.append(sid)
                self.logger.emit(
                    "dependent_unverified", repo_id=repo_id, symbol_id=sid,
                    reason=f"dependency changed within closure depth "
                           f"{closure[sid]} ≤ {cfg.closure_depth} → unverified",
                    seeds=sorted(seeds), repo_version=after,
                )

        # ---- 阶段 D：依赖边刷新（闭包之后，避免切断传播路径）----
        for sid, deps in deps_refresh:
            self.store.set_deps(sid, deps)
            outcome.deps_refreshed.append(sid)
            self.logger.emit(
                "deps_refreshed", repo_id=repo_id, symbol_id=sid, deps=deps,
                reason="resolved dependency set drifted; "
                       "version/validity untouched",
            )

        outcome.repo_version_after = after
        self.store.commit()
        self.logger.emit(
            "sync_completed", repo_id=repo_id,
            repo_version_before=before, repo_version_after=after,
            inserted=outcome.inserted, content_changed=outcome.content_changed,
            reverted=outcome.reverted, tombstoned=outcome.tombstoned,
            unverified=outcome.unverified, unchanged_count=outcome.unchanged_count,
            deps_refreshed=outcome.deps_refreshed,
            skipped_files=outcome.skipped_files,
            parse_warnings=outcome.parse_warnings,
        )
        return outcome

    def verify(self, symbol_id: str, repo_root: str | Path) -> str:
        """显式重哈希校验：unverified → valid；失配 → stale；消失 → tombstoned。"""
        repo_root = Path(repo_root)
        entry = self.store.get(symbol_id)
        if entry is None:
            raise KeyError(f"unknown symbol_id: {symbol_id}")
        if entry.validity == Validity.TOMBSTONED.value:
            return entry.validity
        path = repo_root / entry.file_path
        after = self.store.get_repo_version(entry.repo_id)
        if not path.is_file():
            self.store.tombstone(symbol_id, after + 1)
            self.store.commit()
            self.logger.emit(
                "verify_tombstone", symbol_id=symbol_id, repo_version=after + 1,
                reason="file missing during verify",
            )
            return Validity.TOMBSTONED.value
        language = self.config.supported_languages.get(path.suffix.lower())
        if language is None:
            raise RuntimeError(f"unsupported language: {entry.file_path}")
        drafts, _ = parse_source(
            path.read_bytes(), entry.file_path, entry.repo_id, language
        )
        match = next((d for d in drafts if d.symbol_id == symbol_id), None)
        if match is None:
            self.store.tombstone(symbol_id, after + 1)
            self.store.commit()
            self.logger.emit(
                "verify_tombstone", symbol_id=symbol_id, repo_version=after + 1,
                reason="symbol not found during verify",
            )
            return Validity.TOMBSTONED.value
        if match.content_hash == entry.content_hash:
            self.store.set_validity(symbol_id, Validity.VALID.value)
            self.store.commit()
            self.logger.emit(
                "verify_confirmed", symbol_id=symbol_id,
                reason="rehash matches memory basis content_hash → valid "
                       "(restore protocol)",
            )
            return Validity.VALID.value
        self.store.apply_source_change(
            symbol_id,
            source_hash=match.content_hash,
            version=entry.version + 1,
            validity=Validity.STALE.value,
            size_bytes=match.size_bytes,
            start_line=match.start_line,
            end_line=match.end_line,
            repo_version=after + 1,
            deps=entry.deps,
            summary=entry.summary,
            kv_ptr=entry.kv_ptr,
        )
        self.store.commit()
        self.logger.emit(
            "verify_stale", symbol_id=symbol_id, repo_version=after + 1,
            reason="rehash mismatch vs content_hash → stale",
        )
        return Validity.STALE.value


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
