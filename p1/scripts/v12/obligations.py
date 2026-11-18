"""V13E·S2 义务账本（v2）：窄口径解析 + 只渲染「未结」义务。

背景（设计稿 §2 与筛选发现）：
- harness 逐步丢弃历史 user 指令 → 义务会「蒸发」（DS ind_L06a：step3 要求
  codec.py 新增 encode2/decode2，漏做后再无人提醒，终步 NO_EDIT 级联）。
- **v1 形态（指令全文常驻）实测 +460 tok/集**，在小任务场上净亏 → v2 只留
  未结义务，并按窄口径渲染紧凑行。

判定（全部确定性、零 LLM，基于每步 workspace 快照）：
- 解析：子句含编辑动词且点名 <file.py> → 抽 (file, symbol) 目标；
- add 型（子句含 新增/实现）：当前源码中**符号缺席** → 未结；
- modify 型：自义务提出时起该文件**哈希未变**（从未被改）→ 未结；
- 解析不出目标：保守视为未结，但按 ≤48 字紧凑子句渲染（有界成本）。

一条指令 → 一行；任一目标未结即保留该行。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_EDIT_RE = re.compile(
    r"(修改|新增|删除|实现|重命名|替换|调整|写入|添加|edit|add|remove|implement|fix)",
    re.I,
)
# 强动作：点名文件即视为义务（即便抽不出符号，如常量 RATE）
_STRONG_RE = re.compile(
    r"(修改|新增|删除|重命名|替换|写入|添加|edit|remove)", re.I
)
_NEG_RE = re.compile(r"不要修改|勿改|do not modify", re.I)
_ADD_STRONG_RE = re.compile(r"(新增|添加|写入)", re.I)
_ADD_WEAK_RE = re.compile(r"(实现|implement)", re.I)
_FILE_RE = re.compile(r"([A-Za-z_][\w]*\.py)")
_SYM_AFTER_DE = re.compile(r"中的\s*([A-Za-z_]\w*)")
_SYM_ADD = re.compile(r"(?:新增|实现|添加|写入)\s*([A-Za-z_]\w*)\s*\(")
_SYM_CALL = re.compile(r"([A-Za-z_]\w*)\s*\(")

_RAW_CAP = 48
_CLAUSE_SPLIT = re.compile(r"[。；;\n]")


@dataclass
class Obligation:
    step: int
    text: str  # 原始指令（诊断用）
    clause: str  # 主子句（raw 兜底渲染）
    kind: str  # add | modify | raw
    targets: list[tuple[str, str]] = field(default_factory=list)  # (file, symbol)
    sha_raise: dict[str, str] = field(default_factory=dict)  # 提出时 pre-step sha


def _clauses(instruction: str) -> list[str]:
    return [c.strip() for c in _CLAUSE_SPLIT.split(instruction or "") if c.strip()]


def parse_obligation(step_no: int, instruction: str) -> Obligation:
    """把一步指令解析为单条义务（无目标则 kind=raw）。

    子句准入：点名 <file.py>，且（抽得出符号 或 含强动作动词）。
    弱动词（实现/调整…）仅在抽得出符号时才算义务 —— 避免
    「请参考 biz.py 当前实现。」这类参考句被误判为未结义务。
    """
    instr = instruction or ""
    targets: list[tuple[str, str]] = []
    kind = "raw"
    main_clause = ""
    for cl in _clauses(instr):
        if _NEG_RE.search(cl):
            continue
        if not _EDIT_RE.search(cl):
            continue
        files = _FILE_RE.findall(cl)
        if not files:
            continue
        m = _SYM_AFTER_DE.search(cl) or _SYM_ADD.search(cl) or _SYM_CALL.search(cl)
        sym = m.group(1) if m else None
        if sym and sym.endswith(".py"):
            sym = None
        if not sym and not _STRONG_RE.search(cl):
            continue  # 弱动词 + 无符号 → 参考句，不入账
        if not main_clause:
            main_clause = cl
        # 只取**子句首个文件**为主目标：后续文件多为语境/依赖
        # （例：「gateway.py 新增 route()：用 codec.py 的 decode…」，
        #   若把 route 也挂到 codec.py 上，该义务将永不关闭）
        targets.append((files[0], sym or ""))
        if _ADD_STRONG_RE.search(cl) or (_ADD_WEAK_RE.search(cl) and sym):
            kind = "add"
        elif kind == "raw":
            kind = "modify"
    if not targets:
        # 兜底：取第一条含编辑动词的子句，或首句
        for cl in _clauses(instr):
            if _EDIT_RE.search(cl) and not _NEG_RE.search(cl):
                main_clause = cl
                break
        if not main_clause:
            main_clause = instr
        return Obligation(step=step_no, text=instr, clause=main_clause, kind="raw")
    if kind == "raw":
        kind = "modify"
    return Obligation(
        step=step_no,
        text=instr,
        clause=main_clause or instr,
        kind=kind,
        targets=targets,
    )


def raise_sha(obligation: Obligation, pre_sha: dict[str, str]) -> Obligation:
    """记录义务提出时（该步动作之前）目标文件的哈希。"""
    obligation.sha_raise = {
        f: pre_sha[f] for f, _ in obligation.targets if f in (pre_sha or {})
    }
    return obligation


_WORD_RE_CACHE: dict[str, re.Pattern] = {}


def _word_re(sym: str) -> re.Pattern:
    p = _WORD_RE_CACHE.get(sym)
    if p is None:
        p = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(sym)}(?![A-Za-z0-9_])")
        _WORD_RE_CACHE[sym] = p
    return p


def is_open(
    obligation: Obligation,
    files: dict[str, str],
    sha_now: dict[str, str],
) -> bool:
    """未结判定。files=当前步 workspace 全量源码；sha_now=当前步哈希。"""
    if obligation.kind == "raw" or not obligation.targets:
        return True
    if obligation.kind == "add":
        # 任一目标符号仍缺席 → 未结；无符号可查时回退到「文件是否被改过」
        has_sym = False
        for f, sym in obligation.targets:
            if not sym:
                continue
            has_sym = True
            src = files.get(f, "")
            if src and not _word_re(sym).search(src):
                return True
            if not src:
                return True
        if has_sym:
            return False
        return _sha_untouched(obligation, sha_now)
    # modify：自提出以来从未改过该文件 → 未结
    return _sha_untouched(obligation, sha_now)


def _sha_untouched(obligation: Obligation, sha_now: dict[str, str]) -> bool:
    for f, _ in obligation.targets:
        if f not in obligation.sha_raise:
            return True  # 提出时该文件不存在（新建类）→ 保守未结
        if sha_now.get(f) == obligation.sha_raise[f]:
            return True
    return False


def render_line(obligation: Obligation) -> str:
    """紧凑渲染（不含列表前缀 `- `）。"""
    head = f"[{obligation.step}]"
    if obligation.kind == "raw":
        body = re.sub(r"\s+", " ", obligation.clause).strip()
        if len(body) > _RAW_CAP:
            body = body[:_RAW_CAP] + "…"
        return f"{head} {body}"
    seen: list[str] = []
    files: list[str] = []
    for f, sym in obligation.targets:
        if f not in files:
            files.append(f)
        if sym and sym not in seen:
            seen.append(sym)
    verb = "新增" if obligation.kind == "add" else "修改"
    head_txt = f"{verb} {'/'.join(files)}"
    if seen:
        head_txt += f": {'、'.join(seen)}"
    return f"{head} {head_txt}"


def open_lines(
    obligations: list[Obligation],
    files: dict[str, str],
    sha_now: dict[str, str],
) -> list[str]:
    """只渲染仍未结的义务行（供 build_messages 的 ledger_lines）。"""
    return [render_line(o) for o in obligations if is_open(o, files, sha_now)]
