"""V1.3-M1 adaptive_a features: computed only pre-request from static inputs."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

_WORD_BOUNDARY_FMT = r"(?<![A-Za-z0-9_]){name}(?![A-Za-z0-9_])"


def _boundary_re(name: str) -> re.Pattern:
    return re.compile(_WORD_BOUNDARY_FMT.format(name=re.escape(name)))


@dataclass
class AdaptiveFeature:
    relpath: str
    implementation_body: bool | None  # None = uncomputable
    instruction_hit: bool
    dependency_touch: bool
    upgrade_to_full: bool
    reason: str
    uncomputable_reason: str = ""
    details: dict = field(default_factory=dict)


def has_implementation_body(source: str | None) -> tuple[bool | None, str]:
    """True if AST contains FunctionDef/AsyncFunctionDef/ClassDef.

    Returns (value, reason). value=None when parse fails or source empty.
    """
    if source is None:
        return None, "source_missing"
    if not source.strip():
        return False, "empty_source"
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return None, f"syntax_error:{e.msg}"
    except Exception as e:  # noqa: BLE001
        return None, f"parse_error:{type(e).__name__}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # ignore trivial empty bodies? still counts as implementation site
            return True, "ast_has_def"
    return False, "ast_no_def"


def instruction_hit(
    relpath: str, instruction: str, symbols: list[str] | None = None
) -> tuple[bool, str]:
    """Word-boundary path or symbol mention in instruction (pre-exec)."""
    instr = instruction or ""
    base = relpath.split("/")[-1]
    if base and re.search(
        _WORD_BOUNDARY_FMT.format(name=re.escape(base)), instr
    ):
        return True, "path_token"
    stem = base.rsplit(".", 1)[0] if base else ""
    if stem and len(stem) >= 3 and re.search(
        _WORD_BOUNDARY_FMT.format(name=re.escape(stem)), instr
    ):
        return True, "stem_token"
    for sym in symbols or []:
        if len(sym) >= 2 and re.search(
            _WORD_BOUNDARY_FMT.format(name=re.escape(sym)), instr
        ):
            return True, f"symbol:{sym}"
    return False, "no_hit"


def dependency_touch(
    relpath: str,
    edit_targets: set[str],
    file_deps: dict[str, set[str]],
    *,
    depth: int = 2,
) -> tuple[bool, str]:
    """True if relpath is within depth of edit_targets in provider/caller graph."""
    rel = relpath.replace("\\", "/")
    if not edit_targets:
        return False, "no_edit_targets"
    # providers from targets
    providers: set[str] = set()
    frontier = set(edit_targets)
    for _ in range(max(0, depth)):
        nxt: set[str] = set()
        for f in frontier:
            for p in file_deps.get(f, set()):
                if p not in providers:
                    providers.add(p)
                    nxt.add(p)
        frontier = nxt
    closed = set(edit_targets) | providers
    if rel in closed:
        return True, "in_provider_closure"
    # callers of closed within depth
    reverse: dict[str, set[str]] = {}
    for f, deps in file_deps.items():
        for d in deps:
            reverse.setdefault(d, set()).add(f)
    frontier = set(closed)
    seen_callers: set[str] = set()
    for _ in range(max(0, depth)):
        nxt: set[str] = set()
        for f in frontier:
            for c in reverse.get(f, set()):
                if c not in closed and c not in seen_callers:
                    seen_callers.add(c)
                    nxt.add(c)
        frontier = nxt
    if rel in seen_callers:
        return True, "in_caller_closure"
    return False, "not_in_closure"


def decide_related_level(
    *,
    relpath: str,
    source: str | None,
    instruction: str,
    symbols: list[str] | None,
    edit_targets: set[str],
    file_deps: dict[str, set[str]],
    closure_depth: int = 2,
) -> AdaptiveFeature:
    """adaptive_a: FULL iff impl_body AND (instruction_hit OR dependency_touch).

    Conservative: uncomputable features → Digest (no Full upgrade).
    """
    body, body_reason = has_implementation_body(source)
    ihit, ihit_reason = instruction_hit(relpath, instruction, symbols)
    dtouch, dtouch_reason = dependency_touch(
        relpath, edit_targets, file_deps, depth=closure_depth
    )

    if body is None:
        return AdaptiveFeature(
            relpath=relpath,
            implementation_body=None,
            instruction_hit=ihit,
            dependency_touch=dtouch,
            upgrade_to_full=False,
            reason="conservative_digest_uncomputable",
            uncomputable_reason=body_reason,
            details={"instruction": ihit_reason, "dependency": dtouch_reason},
        )

    if body and (ihit or dtouch):
        why = []
        if ihit:
            why.append(f"instruction_hit:{ihit_reason}")
        if dtouch:
            why.append(f"dependency_touch:{dtouch_reason}")
        return AdaptiveFeature(
            relpath=relpath,
            implementation_body=True,
            instruction_hit=ihit,
            dependency_touch=dtouch,
            upgrade_to_full=True,
            reason="adaptive_a_full:" + ",".join(why),
            details={"body": body_reason},
        )

    if not body:
        reason = "no_implementation_body"
    else:
        reason = "impl_but_no_instruction_or_dep"
    return AdaptiveFeature(
        relpath=relpath,
        implementation_body=body,
        instruction_hit=ihit,
        dependency_touch=dtouch,
        upgrade_to_full=False,
        reason=f"adaptive_a_digest:{reason}",
        details={"body": body_reason, "instruction": ihit_reason, "dependency": dtouch_reason},
    )
