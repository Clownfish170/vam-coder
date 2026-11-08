#!/usr/bin/env python
"""双 Token 策略包装（测试侧，零生产代码修改）——补记冻结 d664d602…

模式（全局 DT_MODE，orchestrator 每集设置）：
  reference      — 不包装（D = Full V12-F 原样）
  symbolic       — B：相关非目标 → 符号 ID 行；指令命中符号 → 函数/常量级源码切片
  static+address — C：相关非目标 → 静态紧凑表示（签名/常量行，file::sym 即 ID）
                   + 指令命中符号完整源码；O′ 保持开启（默认配置）

变换范围（与 V13 的 adaptive 决策同边界）：plan.files 中 level=FULL 且
非 must、非 edit_target、非 candidate 的文件（即"相关非目标"）。
must/ET/C 永远保持全量 FILE 块——VSO 安全条件四组固定。
动态信息：每次装配从**当前工作区**读内容（runner 每步已 sync）→ 更新必达。
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import run_p1_v12 as R

DT_MODE = "reference"  # reference | symbolic | static+address

_FILE_BLOCK_RE = re.compile(
    r"--- FILE (?P<path>[^\n(]+) \(full current source\) ---\n"
    r"(?P<body>[\s\S]*?)(?=\n--- (?:FILE|INDEX|SYMBOL|SYMBOL_SOURCE|STATIC) |\n=== |\Z)"
)


def _boundary_hit(name: str, instruction: str) -> bool:
    if len(name) < 2:
        return False
    return bool(re.search(
        r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", instruction or ""))


def _symbols_of(src: str) -> list[tuple[str, str, bool]]:
    """[(name, source_segment, is_const)] 顶层 def/class/常量赋值。"""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seg = ast.get_source_segment(src, node)
            if seg:
                out.append((node.name, seg, False))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    seg = ast.get_source_segment(src, node)
                    if seg:
                        out.append((t.id, seg, True))
    return out


def _sig_line(name: str, seg: str) -> str:
    first = seg.splitlines()[0].rstrip()
    return first + (" ..." if not first.rstrip().endswith(":") is False else "")


def transform_plan_related(
    workspace: Path,
    text: str,
    plan,
    instruction: str,
    mode: str,
) -> tuple[str, dict]:
    """把相关非目标的 FILE 块替换为 B/C 形式；返回 (new_text, stats)。"""
    transformable = {
        f.relpath for f in plan.files
        if f.level == "FULL" and not f.is_must
        and not f.is_edit_target and not f.is_candidate
    }
    if not transformable or mode == "reference":
        return text, {"mode": mode, "transformed": []}

    matches = list(_FILE_BLOCK_RE.finditer(text))
    if not matches:
        return text, {"mode": mode, "transformed": []}

    preamble = text[: matches[0].start()]
    pieces: list[str] = []
    stats = {"mode": mode, "transformed": [], "symbol_source": [], "static": [], "id_lines": 0}

    def _artifacts(rel: str) -> str:
        ws_file = workspace / rel
        if not ws_file.exists():
            return ""
        src = ws_file.read_text(encoding="utf-8")
        syms = _symbols_of(src)
        parts: list[str] = []
        if mode == "symbolic":
            for name, seg, is_const in syms:
                if _boundary_hit(name, instruction) and not is_const:
                    parts.append(f"--- SYMBOL_SOURCE {rel}::{name} ---\n{seg.rstrip()}\n")
                    stats["symbol_source"].append(f"{rel}::{name}")
                elif _boundary_hit(name, instruction) and is_const:
                    parts.append(f"--- SYMBOL_SOURCE {rel}::{name} ---\n{seg.rstrip()}\n")
                    stats["symbol_source"].append(f"{rel}::{name}")
                else:
                    parts.append(f"--- SYMBOL {rel}::{name} ---")
                    stats["id_lines"] += 1
            if not syms:
                parts.append(f"--- SYMBOL {rel} (no symbols) ---")
                stats["id_lines"] += 1
        else:  # static+address
            lines = []
            for name, seg, is_const in syms:
                if _boundary_hit(name, instruction):
                    lines.append(f"--- SYMBOL_SOURCE {rel}::{name} ---\n{seg.rstrip()}\n")
                    stats["symbol_source"].append(f"{rel}::{name}")
                elif is_const:
                    lines.append(f"--- STATIC {rel}::{seg.splitlines()[0].strip()} ---")
                    stats["static"].append(f"{rel}::{name}")
                else:
                    first = seg.splitlines()[0].rstrip()
                    lines.append(f"--- STATIC {rel}::{first} ... ---")
                    stats["static"].append(f"{rel}::{name}")
            if not syms:
                lines.append(f"--- STATIC {rel} (empty) ---")
                stats["static"].append(f"{rel}::(empty)")
            parts.extend(lines)
        return "\n".join(parts) + "\n"

    for m in matches:
        rel = m.group("path").strip()
        if rel in transformable:
            pieces.append(_artifacts(rel))
            stats["transformed"].append(rel)
        else:
            pieces.append(m.group(0))

    new_text = preamble + "\n".join(p for p in pieces if p)
    if not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, stats


def _count_blocks(text: str) -> tuple[int, int]:
    return (
        len(re.findall(r"--- FILE ", text)),
        len(re.findall(r"--- (?:SYMBOL|SYMBOL_SOURCE|STATIC) ", text)),
    )


# ---------------------------------------------------------------- 包装安装
_ORIG: dict = {}


def install() -> None:
    """安装 build_plan 指令暂存 + assemble 变换包装（进程内）。"""
    if _ORIG:
        return
    _ORIG["build_plan"] = R.build_plan
    _ORIG["assemble_v12"] = R.assemble_v12

    def _bp(**kw):
        plan = _ORIG["build_plan"](**kw)
        plan._dt_instruction = kw.get("instruction", "")
        return plan

    def _asm(workspace, plan, tracker, cfg, **kw):
        ctx = _ORIG["assemble_v12"](workspace, plan, tracker, cfg, **kw)
        if DT_MODE in ("reference", "inline_full") or ctx.insufficient:
            return ctx
        instruction = getattr(plan, "_dt_instruction", "")
        new_text, stats = transform_plan_related(workspace, ctx.text, plan, instruction, DT_MODE)
        if stats.get("transformed"):
            ctx.text = new_text
            fb, dl = _count_blocks(new_text)
            ctx.file_blocks = fb
            ctx.digest_lines = dl
            ctx.notes.append(f"dualtoken_transform:{DT_MODE}:{','.join(stats['transformed'])}")
        return ctx

    R.build_plan = _bp
    R.assemble_v12 = _asm


def restore() -> None:
    if not _ORIG:
        return
    R.build_plan = _ORIG["build_plan"]
    R.assemble_v12 = _ORIG["assemble_v12"]
    _ORIG.clear()


def set_mode(mode: str) -> None:
    global DT_MODE
    DT_MODE = mode


# ---------------------------------------------------------------- dry-run 校验
def validate_task_context(task_dir_steps: list[Path], mode: str, task: str,
                          audits_path: Path) -> list[str]:
    """按步（逐 audit 行）做形态断言；返回问题列表（空=通过）。"""
    problems: list[str] = []
    by_step: dict[str, dict] = {}
    if audits_path.exists():
        for line in audits_path.read_text(encoding="utf-8").splitlines():
            a = json.loads(line)
            by_step[a["step"]] = a
    for sd in task_dir_steps:
        a = by_step.get(sd.name)
        if a is None:
            problems.append(f"{sd.name}: missing injection audit row")
            continue
        ctx = (sd / "context.txt").read_text(encoding="utf-8")
        plan_t = set(a.get("plan", {}).get("edit_targets", []))
        cand = set(a.get("plan", {}).get("candidate_full", []))
        transformable = {
            x["path"] for x in a.get("levels", [])
            if x.get("level") == "FULL" and not x.get("is_must")
            and x["path"] not in plan_t and x["path"] not in cand
        }
        # edit targets 必须在当前 context 全量
        for t in plan_t:
            if f"--- FILE {t} " not in ctx:
                problems.append(f"{sd.name}: edit target {t} 不在 context（违反 E 强制全量）")
        for rel in transformable:
            has_file = f"--- FILE {rel} " in ctx
            has_sym = f"--- SYMBOL" in ctx and rel in ctx
            has_static = f"--- STATIC {rel} " in ctx
            has_src = f"--- SYMBOL_SOURCE {rel}::" in ctx
            if mode == "reference":
                if has_sym or has_static:
                    problems.append(f"{sd.name}: D 模式出现寻址/静态行 {rel}")
            elif mode == "symbolic":
                if has_file:
                    problems.append(f"{sd.name}: B 模式仍内联原文 {rel}")
                if not (has_sym or has_src):
                    problems.append(f"{sd.name}: B 模式缺少符号行 {rel}")
            elif mode == "static+address":
                if has_file:
                    problems.append(f"{sd.name}: C 模式仍内联原文 {rel}")
                if not (has_static or has_src):
                    problems.append(f"{sd.name}: C 模式缺少静态行/命中源码 {rel}")
        if mode == "inline_full":
            # A：不得发生任何 O′ 省略
            for c in a.get("checks", []):
                if c["action"] == "REUSE_KV":
                    problems.append(f"{sd.name}: A 模式出现 REUSE_KV {c['file']}")
            # A：可变换集应保持全量内联
            for rel in transformable:
                if f"--- FILE {rel} " not in ctx:
                    problems.append(f"{sd.name}: A 模式未内联相关文件 {rel}")
    return problems
