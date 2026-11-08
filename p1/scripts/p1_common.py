"""P1 实验公共组件：模型客户端、四种基线的上下文装配、编辑应用、隔离评测。

能力边界（写入运行元数据，供论文/报告核对）：
- 本模块不实现真实 KV Cache 存储；vam_coder 基线中 REUSE_KV 的省略是
  “多轮对话前缀复用”代理：仅当该符号当前内容哈希与对话中已发送内容一致
  时才省略。llama-server / Ollama 对多轮前缀有真实的服务端 KV 复用，但
  这不等同于 VAM 论文中的跨请求记忆 KV 仓。
- EXPAND/COMPRESS/DROP 语义来自冻结的 P0 路由器；本模块只负责按决策装配
  文本上下文并测量，不修改 P0 源码。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

SYSTEM_PROMPT = (
    "You are a careful code editor working on a small Python repository.\n"
    "Each turn you receive one task and (depending on the agent's memory mode)\n"
    "some repository context.\n"
    "Reply ONLY with the files you change, using exactly this format:\n\n"
    "FILE: relative/path.py\n"
    "```python\n"
    "<full new content of the file>\n"
    "```\n\n"
    "Rules:\n"
    "- Output complete file contents, not diffs.\n"
    "- Change only what the task requires.\n"
    "- Do not invent new files unless the task requires it.\n"
    "- If no change is needed, reply exactly: NO_EDIT\n"
)


def posix(path: str) -> str:
    """Windows 路径规范化：统一为 posix 分隔符（P1 兼容性修补）。"""
    return str(path).replace("\\", "/")


# ---------------------------------------------------------------- HTTP 客户端
@dataclass
class ChatResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    usage_source: str
    raw_usage: dict = field(default_factory=dict)
    error: str | None = None
    # v0.2：请求级审计字段（不保存任何鉴权头/密钥）
    http_status: int | None = None
    response_model: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def chat_completion(
    endpoint: str,
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    timeout: float = 300.0,
    seed: int | None = 0,
) -> ChatResult:
    """OpenAI 兼容 /chat/completions 客户端（llama-server、Ollama /v1 均可用）。

    脱敏：不记录请求头；本客户端不发送 Authorization。服务端不提供的
    usage 字段保持缺失（raw_usage 原样保存），不做任何伪造。
    """
    url = endpoint.rstrip("/") + "/chat/completions"
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if seed is not None:
        payload["seed"] = seed
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    # 可选鉴权（round3 云端端点）：仅当环境变量存在时附加；本地 llama-server
    # 无该变量 → 行为与历史轮完全一致。密钥不写入任何日志/产物。
    _api_key = os.environ.get("VAM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if _api_key:
        headers["Authorization"] = f"Bearer {_api_key}"
    req = urllib.request.Request(url, data=data, headers=headers)
    started_at = _iso_now()
    t0 = time.perf_counter()
    http_status: int | None = None
    body: dict | None = None
    err: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            http_status = getattr(resp, "status", None)
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        http_status = exc.code
        err = f"HTTPError: {exc.code} {exc.reason}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        err = f"{type(exc).__name__}: {exc}"
    latency_ms = (time.perf_counter() - t0) * 1000.0
    ended_at = _iso_now()

    if body is None:
        return ChatResult(
            text="",
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=latency_ms,
            usage_source="none",
            error=err,
            http_status=http_status,
            response_model=None,
            started_at=started_at,
            ended_at=ended_at,
        )
    try:
        text = body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        text = ""
    usage = body.get("usage") or {}
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    source = "api" if (pt or ct) else "estimate"
    if source == "estimate":
        pt = estimate_tokens(messages)
        ct = max(1, len(text) // 4)
    return ChatResult(
        text=text,
        prompt_tokens=pt,
        completion_tokens=ct,
        latency_ms=latency_ms,
        usage_source=source,
        raw_usage=usage,
        error=err,
        http_status=http_status,
        response_model=body.get("model"),
        started_at=started_at,
        ended_at=ended_at,
    )


def estimate_tokens(messages: list[dict]) -> int:
    chars = sum(len(m.get("content") or "") for m in messages)
    return max(1, chars // 4)


# ------------------------------------------------------------ 编辑解析与应用
_FENCE_RE = re.compile(r"^\s*```")


def parse_file_blocks(text: str) -> list[tuple[str, str]]:
    """解析 `FILE: path` + 下一个 ``` 围栏块 → [(relpath, content)]。"""
    lines = text.splitlines()
    blocks: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^\s*FILE:\s*(.+?)\s*$", lines[i])
        if not m:
            i += 1
            continue
        rel = m.group(1).strip().strip("`").strip('"').strip("'")
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and _FENCE_RE.match(lines[j]):
            j += 1
            buf: list[str] = []
            while j < len(lines) and not _FENCE_RE.match(lines[j]):
                buf.append(lines[j])
                j += 1
            blocks.append((rel, "\n".join(buf).rstrip() + "\n"))
            i = j + 1
        else:
            i += 1
    return blocks


def apply_blocks(
    workspace: Path, blocks: list[tuple[str, str]]
) -> tuple[list[str], list[dict]]:
    """把 FILE 块写入工作区；拒绝越界路径/非 .py 文件。"""
    ws = Path(workspace).resolve()
    applied: list[str] = []
    rejected: list[dict] = []
    for rel, content in blocks:
        # 注意：不能用 lstrip("./")——会把 "../x" 与 "/x" 洗成工作区内路径
        rel_n = posix(rel).strip()
        while rel_n.startswith("./"):
            rel_n = rel_n[2:]
        if (
            not rel_n.endswith(".py")
            or rel_n.startswith("/")
            or rel_n.startswith("../")
            or rel_n == ".."
            or ".." in rel_n.split("/")
            or ":" in rel_n.split("/")[0]
        ):
            rejected.append({"path": rel_n, "reason": "path not allowed"})
            continue
        target = (ws / rel_n).resolve()
        if not str(target).startswith(str(ws) + os.sep) and target != ws:
            rejected.append({"path": rel_n, "reason": "outside workspace"})
            continue
        if "eval/" in rel_n or rel_n.startswith("eval"):
            rejected.append({"path": rel_n, "reason": "eval dir is protected"})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        applied.append(rel_n)
    return applied, rejected


# ---------------------------------------------------------------- 评测
def run_eval(workspace: Path, eval_dir: Path, timeout: float = 180.0) -> tuple[bool, str]:
    """把 eval 目录复制到临时目录运行，测试与模型可写工作区隔离。"""
    ws = Path(workspace).resolve()
    with tempfile.TemporaryDirectory(prefix="p1_eval_") as td:
        dest = Path(td) / "eval"
        shutil.copytree(eval_dir, dest)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ws) + os.pathsep + env.get("PYTHONPATH", "")
        env.pop("PYTEST_CURRENT_TEST", None)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short", "eval"],
                cwd=td,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False, f"EVAL_TIMEOUT after {timeout}s"
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        return proc.returncode == 0, out.strip()


# ------------------------------------------------------- 上下文装配（四基线）
@dataclass
class AssembledContext:
    text: str
    # 复用量三口径（任务 7）：决策级 / 文件级实际省略 / 未产生省略的决策
    reuse_omitted: int = 0            # 文件级实际省略的符号数（哈希命中且整文件未展开）
    reuse_decisions: int = 0          # 决策级 REUSE_KV 次数（含同文件被 EXPAND 带回的）
    reuse_omitted_files: int = 0      # 完全省略的文件数
    reuse_omitted_bytes: int = 0      # 完全省略文件的字节数（理论可省略内容规模）
    reuse_without_omission: int = 0   # REUSE_KV 决策但因同文件 EXPAND 未产生省略
    expand_included_bytes: int = 0    # 因 EXPAND/回退读取而纳入的文件字节数
    summary_bytes: int = 0            # COMPRESS 摘要文本字节数
    file_blocks: int = 0
    summary_blocks: int = 0
    notes: list[str] = field(default_factory=list)
    # v1.0 审计：逐文件 assemble_audit 与谓词计数
    assemble_audit: list = field(default_factory=list)
    n_verified_safe_omissions: int = 0


def _file_block(rel: str, content: str) -> str:
    return f"--- FILE {rel} (full current source) ---\n{content.rstrip()}\n"


def _summary_block(
    qualified: str, symbol_id: str, validity: str, summary: str, frozen: bool
) -> str:
    tag = "frozen at episode start" if frozen else "memory note"
    return (
        f"--- MEMORY SUMMARY ({tag}): {qualified} "
        f"[{symbol_id}; validity={validity}] ---\n{(summary or '').strip()}\n"
    )


def _read_workspace_files(workspace: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for p in sorted(workspace.rglob("*.py")):
        rel = posix(p.relative_to(workspace))
        if rel.startswith("eval/") or "/__pycache__/" in f"/{rel}":
            continue
        try:
            files[rel] = p.read_text(encoding="utf-8")
        except OSError:
            continue
    return files


def assemble_memory_off(workspace: Path, extra_note: str = "") -> AssembledContext:
    files = _read_workspace_files(workspace)
    parts = [
        "[MODE] memory_off: no persistent memory; full current repository source is provided each step."
    ]
    if extra_note:
        parts.append(extra_note)
    total_bytes = 0
    for rel, content in files.items():
        parts.append(_file_block(rel, content))
        total_bytes += len(content.encode("utf-8"))
    ctx = AssembledContext(
        text="\n".join(parts) + "\n",
        file_blocks=len(files),
        expand_included_bytes=total_bytes,
        notes=["full_repo_files"],
    )
    return ctx


def assemble_symbol_full_read(
    workspace: Path, symbol_files: list[str]
) -> AssembledContext:
    """符号级全量重读：索引中每个存活符号的所在文件完整源码，每步重发。"""
    files = _read_workspace_files(workspace)
    parts = [
        "[MODE] symbol_full_read: every indexed symbol is re-read in full each step "
        "(no versioning, no reuse)."
    ]
    used = 0
    total_bytes = 0
    for rel in sorted(set(symbol_files)):
        if rel in files:
            parts.append(_file_block(rel, files[rel]))
            used += 1
            total_bytes += len(files[rel].encode("utf-8"))
    return AssembledContext(
        text="\n".join(parts) + "\n",
        file_blocks=used,
        expand_included_bytes=total_bytes,
        notes=["full_symbol_files"],
    )


def assemble_fixed_summary(
    frozen_summaries: dict[str, dict], extra_note: str = ""
) -> AssembledContext:
    parts = [
        "[MODE] fixed_summary: frozen memory summaries only; source is NOT provided "
        "and summaries never refresh after the episode starts."
    ]
    if extra_note:
        parts.append(extra_note)
    n = 0
    nbytes = 0
    for sid in sorted(frozen_summaries):
        rec = frozen_summaries[sid]
        block = _summary_block(
            rec["qualified_name"], sid, rec["validity"],
            rec["summary"], frozen=True,
        )
        parts.append(block)
        nbytes += len(block.encode("utf-8"))
        n += 1
    return AssembledContext(
        text="\n".join(parts) + "\n",
        summary_blocks=n,
        summary_bytes=nbytes,
        notes=["frozen_summaries"],
    )


def assemble_refreshed_summary(summaries: dict[str, dict]) -> AssembledContext:
    """对照 B：每步刷新的摘要，无源码、无版本失效门控（tombstone 除外）。"""
    parts = [
        "[MODE] refreshed_summary (control): summaries refreshed each step from "
        "the current source; source is NOT provided; no version-aware gating."
    ]
    n = 0
    nbytes = 0
    for sid in sorted(summaries):
        rec = summaries[sid]
        block = _summary_block(
            rec["qualified_name"], sid, rec["validity"],
            rec["summary"], frozen=False,
        )
        parts.append(block)
        nbytes += len(block.encode("utf-8"))
        n += 1
    return AssembledContext(
        text="\n".join(parts) + "\n",
        summary_blocks=n,
        summary_bytes=nbytes,
        notes=["refreshed_summaries"],
    )


def assemble_vam_coder(
    workspace: Path,
    decisions: list[dict],
    entries_by_id: dict[str, object],
    history_sent: dict[str, str],
    *,
    chars_per_token: int = 4,
) -> AssembledContext:
    """按 P0 决策装配；REUSE_KV 仅在对话中已有相同哈希内容时才省略。

    同一文件内多个符号共享一次全文件读取（EXPAND/回退读取按文件去重）。
    复用量三口径见 AssembledContext 字段注释；决策次数不等于 token 节省，
    实际收益以最终请求的 API token 统计为准。
    """
    files = _read_workspace_files(workspace)
    history_sent_before = dict(history_sent)
    parts = [
        "[MODE] vam_coder: context assembled by version-aware routing "
        "(EXPAND=full source, COMPRESS=summary, REUSE_KV=omitted when the exact "
        "content is already in this conversation, DROP=omitted)."
    ]
    ctx = AssembledContext(text="")
    by_file: dict[str, list[tuple[dict, object]]] = {}
    for d in decisions:
        e = entries_by_id.get(d["symbol_id"])
        if e is None:
            continue
        by_file.setdefault(posix(e.file_path), []).append((d, e))

    touched_files: set[str] = set()
    omitted_sids: list[str] = []
    for rel in sorted(by_file):
        pairs = by_file[rel]
        actions = [d["action"] for d, _ in pairs]
        ctx.reuse_decisions += sum(1 for a in actions if a == "REUSE_KV")
        need_source = any(a == "EXPAND" for a in actions)
        reuse_mismatch = any(
            a == "REUSE_KV" and history_sent.get(e.symbol_id) != e.source_hash
            for a, (d, e) in zip(actions, pairs)
        )
        file_included = need_source or reuse_mismatch
        if file_included:
            content = files.get(rel, f"# missing file: {rel}\n")
            parts.append(_file_block(rel, content))
            ctx.file_blocks += 1
            touched_files.add(rel)
            ctx.expand_included_bytes += len(content.encode("utf-8"))
            # 决策为 REUSE_KV 且哈希命中，但同文件被展开 → 未产生省略
            ctx.reuse_without_omission += sum(
                1
                for a, (d, e) in zip(actions, pairs)
                if a == "REUSE_KV"
                and history_sent.get(e.symbol_id) == e.source_hash
            )
        else:
            file_bytes = len(files.get(rel, "").encode("utf-8"))
            live = [
                (a, e) for a, (d, e) in zip(actions, pairs) if a != "DROP"
            ]
            omitted_here = [
                e.symbol_id
                for a, e in live
                if a == "REUSE_KV"
                and history_sent.get(e.symbol_id) == e.source_hash
            ]
            omitted_sids.extend(omitted_here)
            if live and len(omitted_here) == len(live):
                ctx.reuse_omitted_files += 1
                ctx.reuse_omitted_bytes += file_bytes
        for a, (d, e) in zip(actions, pairs):
            if a == "COMPRESS":
                block = _summary_block(
                    e.qualified_name, e.symbol_id, e.validity,
                    e.summary, frozen=False,
                )
                parts.append(block)
                ctx.summary_blocks += 1
                ctx.summary_bytes += len(block.encode("utf-8"))
    ctx.reuse_omitted = len(omitted_sids)
    ctx.text = "\n".join(parts) + "\n"
    ctx.notes.append(
        f"reuse_decisions={ctx.reuse_decisions};"
        f"reuse_omitted_symbols={ctx.reuse_omitted};"
        f"reuse_omitted_files={ctx.reuse_omitted_files};"
        f"reuse_omitted_bytes={ctx.reuse_omitted_bytes};"
        f"reuse_without_omission={ctx.reuse_without_omission};"
        f"expand_included_bytes={ctx.expand_included_bytes};"
        f"chars_per_token={chars_per_token}"
    )
    # 更新对话发送记录：本次包含完整源码的文件，其所有符号视为已发送
    for sid, e in entries_by_id.items():
        if posix(e.file_path) in touched_files:
            history_sent[sid] = e.source_hash
    ctx.assemble_audit = _build_assemble_audit(
        by_file, history_sent_before, files, touched_files, chars_per_token
    )
    ctx.n_verified_safe_omissions = sum(
        1 for a in ctx.assemble_audit if a["verified_safe_omission"]
    )
    return ctx


def _build_assemble_audit(
    by_file: dict[str, list[tuple[dict, object]]],
    history_before: dict[str, str],
    files: dict[str, str],
    touched_files: set[str],
    chars_per_token: int,
) -> list[dict]:
    """逐文件审计：O = V1∧V2∧V3∧V4∧V5；O=false 时 omitted_* 必须为 0。"""
    audit: list[dict] = []
    for rel in sorted(by_file):
        pairs = by_file[rel]
        live = [(d, e) for d, e in pairs if d["action"] != "DROP"]
        decisions = []
        for d, e in pairs:
            prev = history_before.get(e.symbol_id)
            decisions.append({
                "symbol_id": e.symbol_id,
                "action": d["action"],
                "history_match": (
                    None if prev is None else prev == e.source_hash
                ),
                "previously_sent": prev is not None,
            })
        live_dec = [x for x in decisions if x["action"] != "DROP"]
        v1 = any(x["action"] == "REUSE_KV" for x in live_dec)
        v2 = bool(live_dec) and all(x["history_match"] is True for x in live_dec)
        v3 = bool(live_dec) and all(x["previously_sent"] for x in live_dec)
        included = rel in touched_files
        v4 = not included
        content = files.get(rel, "")
        nbytes = len(content.encode("utf-8")) if not included else 0
        v5 = nbytes > 0
        verified = bool(v1 and v2 and v3 and v4 and v5)
        audit.append({
            "file": rel,
            "decisions": decisions,
            "hash_match_all": v2,
            "previously_sent": v3,
            "included": included,
            "omitted_bytes": nbytes if verified else 0,
            "omitted_tokens_est": (
                nbytes // max(1, chars_per_token) if verified else 0
            ),
            "verified_safe_omission": verified,
        })
    return audit


def redact_assistant_code(messages: list[dict]) -> list[dict]:
    """条件 M：把 assistant 消息中的 FILE 围栏块替换为占位符（统一脱敏）。"""
    pattern = re.compile(
        r"FILE:\s*(?P<path>[^\n]+)\n```[^\n]*\n(?P<body>[\s\S]*?)```"
    )
    out: list[dict] = []
    for m in messages:
        if m.get("role") != "assistant":
            out.append(dict(m))
            continue
        content = m.get("content") or ""

        def _sub(mo: "re.Match[str]") -> str:
            n = len(mo.group(0))
            return f"FILE: {mo.group('path').strip()} [redacted, {n} chars]"

        out.append({**m, "content": pattern.sub(_sub, content)})
    return out


def history_code_metrics(history: list[dict]) -> dict:
    """历史中 FILE 块数量与 assistant 代码字符数（估算稀释效应用）。"""
    n_blocks = 0
    code_chars = 0
    for m in history:
        if m.get("role") != "assistant":
            continue
        content = m.get("content") or ""
        matches = list(
            re.finditer(
                r"FILE:\s*[^\n]+\n```[^\n]*\n([\s\S]*?)```", content
            )
        )
        n_blocks += len(matches)
        code_chars += sum(len(mo.group(1)) for mo in matches)
    return {"history_file_blocks": n_blocks, "history_code_chars": code_chars}


def trim_history(
    history: list[dict], max_history_chars: int
) -> tuple[list[dict], int, int]:
    """统一历史策略：system 与最新消息永不裁剪；从最旧的 user+assistant 对
    开始成对丢弃，直到历史字符数 ≤ 预算。

    四个基线调用同一函数（同一预算、同一截断规则）。返回
    (trimmed_history, dropped_pairs, history_chars)。
    """
    if max_history_chars <= 0:
        return list(history), 0, 0
    system = [m for m in history if m.get("role") == "system"]
    rest = [m for m in history if m.get("role") != "system"]
    dropped = 0

    def _chars(msgs: list[dict]) -> int:
        return sum(len(m.get("content") or "") for m in msgs)

    while rest and _chars(system + rest) > max_history_chars and len(rest) >= 2:
        rest = rest[2:]
        dropped += 1
    trimmed = system + rest
    return trimmed, dropped, _chars(trimmed)


def tokens_estimate_chars(text: str, chars_per_token: int = 4) -> int:
    """chars/4 类估算，仅用于分解展示；不得当作 API 真实 token。"""
    return max(0, len(text) // max(1, chars_per_token))


def build_messages(
    history: list[dict], instruction: str, context_text: str
) -> list[dict]:
    user = (
        f"=== TASK ===\n{instruction.strip()}\n\n"
        f"=== CONTEXT ===\n{context_text.strip()}\n\n"
        "=== OUTPUT FORMAT ===\n"
        "Respond only with FILE: blocks (or NO_EDIT)."
    )
    return history + [
        {"role": "user", "content": user},
    ]


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"
    )
