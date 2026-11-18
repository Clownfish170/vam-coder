"""ICG：Information-Coverage Greedy — 相关非目标可选 FULL 的子模选择。

设计（不改 VSO / E/C/must 语义）：
- 候选 = plan 中 level=FULL 且非 must/ET/C 的相关非目标
- 效用（次模、单调近似）：
    U(S) = Σ_{f∈S} [ w_hit·hit(f,τ) + w_dep·dep(f, E∪M) + w_r·r(f) + w_x·extract(f,τ) ]
           − λ · Σ_{f∈S} size_tok(f)
- 约束：extract-intent 命中 → **硬约束必须入选**；预算 budget_opt_tokens
- 求解：按边际增益/体积贪心（确定性，可单测）
- 入选 → 保持 FULL（既有 FILE 路径）；落选 → 降为 NONE（跳过注入）

与 F（全 related FULL）、CR-skip（全 related 跳过）形成三点对照。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# 取值/落地类意图：需要看到 related 文件正文才能完成
_EXTRACT_RE = re.compile(
    r"(写死|抄写|抄到|复制到|复制为|读取.*值|取出.*值|查看.*值|"
    r"使用.{0,12}中的值|替换为.{0,16}中的|按.{0,10}中的常量|"
    r"hardcode|copy the value|read the value)",
    re.I,
)
# 明确“参考/依据”但不一定要正文数值（弱 hit）
_REF_RE = re.compile(r"(参考|依据|according to|refer to)", re.I)


@dataclass
class ICGCandidate:
    path: str
    size_bytes: int
    r_score: int = 0
    instruction_hit: bool = False
    dep_touch: bool = False
    extract_intent: bool = False
    # 可选：指令中出现的符号（词界）
    hit_symbols: list[str] = field(default_factory=list)


@dataclass
class ICGResult:
    selected: set[str]
    skipped: set[str]
    forced_extract: set[str]
    audit: list[dict] = field(default_factory=list)
    total_selected_tokens: int = 0


def detect_extract_intent(instruction: str) -> bool:
    return bool(_EXTRACT_RE.search(instruction or ""))


def path_extract_intent(path: str, instruction: str) -> bool:
    """文件是否处于“取值”意图管辖：extract 动词所在子句提到该文件/stem。"""
    instr = instruction or ""
    if not detect_extract_intent(instr):
        return False
    # 子句切分
    clauses = re.split(r"[。；;\n]", instr)
    base = path.split("/")[-1]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    for cl in clauses:
        if not _EXTRACT_RE.search(cl):
            continue
        if base in cl or (len(stem) >= 3 and stem in cl):
            return True
    return False


def _marginal_gain(
    c: ICGCandidate,
    selected: set[str],
    instruction: str,
    *,
    w_hit: float = 2.0,
    w_dep: float = 1.5,
    w_r: float = 1.0,
    w_x: float = 3.0,
    w_ref: float = 0.15,
    lam: float = 0.02,
) -> float:
    """ΔU（比值按体积归一）。

    1.5B 教训：纯「参考 x.py」不足以证明需要 related 正文 → 权重极低；
    取值写死 / 依赖邻接才值得 FULL。
    """
    if c.path in selected:
        return float("-inf")
    gain = 0.0
    if c.extract_intent or path_extract_intent(c.path, instruction):
        gain += w_x
    if c.dep_touch:
        gain += w_dep
    if c.instruction_hit:
        # 编辑子句命中 → 高；正向「参考/依据」子句 → 中（足以过 min_gain=1）
        # 纯否定提及已在 _instr_hits_file 排除
        if _hit_in_edit_clause(c.path, instruction):
            gain += w_hit
        elif _hit_in_ref_clause(c.path, instruction):
            gain += max(w_ref, 1.5)
        else:
            gain += w_ref
    gain += w_r * max(0, c.r_score) * 0.25  # r 仅轻微偏好，避免 related 全选
    # 最小增益阈值：弱 r 不足以证明需要 related 正文
    if gain < 1.0:
        return 0.0
    size_tok = max(1, c.size_bytes // 4)
    return gain / (1.0 + lam * size_tok)


def _hit_in_ref_clause(path: str, instruction: str) -> bool:
    """文件出现在「参考/依据/according to」子句（非否定）。"""
    base = path.split("/")[-1]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    ref_re = re.compile(r"(参考|依据|according to|refer to|查看|读取)", re.I)
    for cl in re.split(r"[。；;\n]", instruction or ""):
        if re.search(r"不要修改|勿改|do not modify", cl, re.I):
            continue
        if not ref_re.search(cl):
            continue
        if base in cl:
            return True
        if len(stem) >= 3 and re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(stem)}(?![A-Za-z0-9_])", cl
        ):
            return True
    return False


def symbolic_use_suppress(
    path: str,
    instruction: str,
    *,
    target_sources: dict[str, str] | None = None,
) -> bool:
    """架构规则：符号化使用 → 抑制 related 全文注入。

    条件（全部满足才抑制）：
      1) 非 extract（没有写死/取值意图）
      2) 指令只「参考」该文件（或仅弱提及），没有编辑该文件
      3) 编辑目标源码存在 `from <stem> import` / `import <stem>`（符号化使用）
         —— 模型可写 `x * RATE` 而无需看到 RATE=10；eval 从磁盘 import，不依赖 context

    返回 True = 不应因「参考」而强制 FULL。
    """
    if path_extract_intent(path, instruction):
        return False
    if _hit_in_edit_clause(path, instruction):
        return False
    base = path.split("/")[-1]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    if len(stem) < 2:
        return False
    # 必须有「参考」弱命中或 r 来自提及；无 target_sources 时：仅当在 ref 子句
    in_ref = _hit_in_ref_clause(path, instruction)
    if not in_ref:
        # 无明确参考也不编辑 → 交给默认低增益（本来就倾向 skip）
        return True
    if not target_sources:
        # 无源码可查 import：保守不抑制（可能需要正文）
        return False
    pat = re.compile(
        rf"(?:from\s+{re.escape(stem)}\s+import|import\s+{re.escape(stem)}\b)"
    )
    for src in target_sources.values():
        if src and pat.search(src):
            return True
    return False


def _hit_in_edit_clause(path: str, instruction: str) -> bool:
    base = path.split("/")[-1]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    edit_re = re.compile(
        r"(修改|新增|删除|重命名|实现|写死|替换|edit|add|remove|rename|implement|fix)",
        re.I,
    )
    for cl in re.split(r"[。；;\n]", instruction or ""):
        if re.search(r"不要修改|勿改|do not modify", cl, re.I):
            continue
        if not edit_re.search(cl):
            continue
        if base in cl:
            return True
        if len(stem) >= 3 and re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(stem)}(?![A-Za-z0-9_])", cl
        ):
            return True
    return False


def select_optional_full(
    candidates: list[ICGCandidate],
    *,
    instruction: str,
    budget_tokens: int = 512,
    forced_paths: set[str] | None = None,
) -> ICGResult:
    """确定性贪心选择。

    forced_paths：硬约束（extract 等）必须入选，不受预算拒绝——预算不足时
    仍保留 forced，并记 audit.over_budget_forced。
    """
    forced = set(forced_paths or ())
    # 自动 extract 硬约束
    for c in candidates:
        if c.extract_intent or path_extract_intent(c.path, instruction):
            forced.add(c.path)

    selected: set[str] = set()
    audit: list[dict] = []
    total_tok = 0

    # 1) 先放 forced（按体积升序，保证小文件优先占预算）
    by_path = {c.path: c for c in candidates}
    for p in sorted(forced, key=lambda x: by_path[x].size_bytes if x in by_path else 0):
        if p not in by_path:
            continue
        c = by_path[p]
        tok = max(1, c.size_bytes // 4)
        selected.add(p)
        total_tok += tok
        audit.append({"path": p, "action": "force_extract", "tokens": tok})

    # 2) 贪心补满预算
    remaining = [c for c in candidates if c.path not in selected]
    while remaining:
        best = None
        best_ratio = float("-inf")
        for c in remaining:
            ratio = _marginal_gain(c, selected, instruction)
            # 确定性 tie-break：path 字典序
            if ratio > best_ratio or (
                ratio == best_ratio and best is not None and c.path < best.path
            ):
                best_ratio = ratio
                best = c
        if best is None or best_ratio <= 0:
            break
        tok = max(1, best.size_bytes // 4)
        if total_tok + tok > budget_tokens:
            # 尝试下一个小体积
            remaining = [c for c in remaining if c.path != best.path]
            # 标记超预算跳过
            audit.append(
                {
                    "path": best.path,
                    "action": "budget_skip",
                    "tokens": tok,
                    "ratio": round(best_ratio, 4),
                }
            )
            # 继续找更小的
            remaining.sort(key=lambda c: (c.size_bytes, c.path))
            # 若最大剩余都放不下则停
            if remaining and max(1, remaining[0].size_bytes // 4) + total_tok > budget_tokens:
                for c in remaining:
                    audit.append(
                        {"path": c.path, "action": "budget_skip", "tokens": max(1, c.size_bytes // 4)}
                    )
                break
            continue
        selected.add(best.path)
        total_tok += tok
        audit.append(
            {
                "path": best.path,
                "action": "greedy_select",
                "tokens": tok,
                "ratio": round(best_ratio, 4),
            }
        )
        remaining = [c for c in remaining if c.path != best.path]

    all_paths = {c.path for c in candidates}
    skipped = all_paths - selected
    for p in sorted(skipped):
        if not any(a.get("path") == p for a in audit):
            audit.append({"path": p, "action": "greedy_skip"})

    return ICGResult(
        selected=selected,
        skipped=skipped,
        forced_extract=forced & all_paths,
        audit=audit,
        total_selected_tokens=total_tok,
    )


def apply_icg_to_plan(plan, instruction: str, *, budget_tokens: int = 512) -> ICGResult:
    """将 ICG 结果写回 ExpandPlan：落选 optional FULL → NONE。

    不得改动 must / edit_targets / candidate_full。
    """
    cands: list[ICGCandidate] = []
    for fl in plan.files:
        if fl.level != "FULL":
            continue
        if fl.is_must or fl.is_edit_target or fl.is_candidate:
            continue
        # relpath
        path = fl.relpath.replace("\\", "/")
        size = 0
        # 尺寸：优先用 plan 侧无 size 时用 r 相关粗估——由调用方传入更好
        size = int(getattr(fl, "size_bytes", 0) or 0)
        if size <= 0:
            # 粗估：无法得知时用 200B 默认（调用应传 size）
            size = 200
        cands.append(
            ICGCandidate(
                path=path,
                size_bytes=size,
                r_score=int(getattr(fl, "r_score", 0) or 0),
                instruction_hit=_instr_hits_file(path, instruction),
                dep_touch=bool(getattr(fl, "is_must", False)),
                extract_intent=path_extract_intent(path, instruction),
            )
        )

    # dep_touch：与 must 有文件级粗关联（路径名出现在 must 邻域由调用方增强）
    result = select_optional_full(
        cands,
        instruction=instruction,
        budget_tokens=budget_tokens,
    )

    for fl in plan.files:
        if fl.level != "FULL":
            continue
        if fl.is_must or fl.is_edit_target or fl.is_candidate:
            continue
        path = fl.relpath.replace("\\", "/")
        if path not in result.selected:
            fl.level = "NONE"
            fl.reason = "icg_skip"
        else:
            fl.reason = "icg_full"
            plan.rules.append(f"icg_full:{path}")
    plan.rules.append(f"icg_selected={len(result.selected)}")
    plan.rules.append(f"icg_skipped={len(result.skipped)}")
    return result


def _instr_hits_file(path: str, instruction: str) -> bool:
    base = path.split("/")[-1]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    instr = instruction or ""
    # 仅正向（非“不要修改”子句）由调用方保证——此处做词界
    if base and re.search(rf"(?<![A-Za-z0-9_]){re.escape(base)}(?![A-Za-z0-9_])", instr):
        # 排除纯否定子句
        for cl in re.split(r"[。；;\n]", instr):
            if base in cl and re.search(r"不要修改|勿改|do not modify", cl, re.I):
                continue
            if base in cl:
                return True
        return False
    if len(stem) >= 3 and re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(stem)}(?![A-Za-z0-9_])", instr
    ):
        for cl in re.split(r"[。；;\n]", instr):
            if stem in cl and re.search(r"不要修改|勿改|do not modify", cl, re.I):
                continue
            if stem in cl:
                return True
    return False
