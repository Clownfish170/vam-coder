"""符号解析：Tree-sitter 提取函数/类/方法及依赖（当前仅支持 Python）。

语言支持限制（P0 实测边界，务必与 config.supported_languages 保持一致）：
- 已支持：.py（tree-sitter-python 语法）
- 不支持：.js/.ts/.java/.go/.rs/.c/.cpp 等（本环境未安装对应 grammar），
  解析时按扩展名记入 ParseResult.skipped_files，reason=unsupported_language。
- Python 内部限制：仅提取模块级函数、类、类方法；函数内嵌套函数/嵌套类
  不作为独立符号（其调用计入外层符号依赖）；依赖解析基于名称消解，
  不做完整 import 语义解析，重名且跨文件歧义的调用记入 unresolved_calls。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tree_sitter import Language, Node, Parser

from .config import AppConfig
from .hashing import content_hash
from .models import SymbolDraft, SymbolKind

# 认得出但本环境无 grammar 的常见源码扩展名 → 明确记录限制
UNSUPPORTED_CODE_SUFFIXES = {
    ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cc", ".cpp",
    ".h", ".hpp", ".rb", ".php", ".cs", ".swift", ".kt", ".scala", ".m", ".mm",
    ".sh", ".pl", ".lua", ".r",
}
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mimocode",
             ".playwright-cli", ".pytest_cache"}

_parsers: dict[str, Parser] = {}


def _get_parser(language: str) -> Parser:
    if language not in _parsers:
        if language != "python":
            raise RuntimeError(f"no grammar registered for language {language!r}")
        import tree_sitter_python

        lang = Language(tree_sitter_python.language())
        _parsers[language] = Parser(lang)
    return _parsers[language]


@dataclass
class ParseResult:
    symbols: list[SymbolDraft] = field(default_factory=list)
    skipped_files: list[dict] = field(default_factory=list)
    parse_warnings: list[dict] = field(default_factory=list)
    unresolved_calls: list[dict] = field(default_factory=list)


def _walk_calls(node: Node, out: list[Node]) -> None:
    if node.type == "call":
        out.append(node)
    for child in node.children:
        _walk_calls(child, out)


def _call_text(call: Node) -> str | None:
    fn = call.child_by_field_name("function")
    if fn is None:
        return None
    if fn.type in ("identifier", "attribute"):
        text = fn.text
        if isinstance(text, bytes):
            return text.decode("utf-8", errors="replace")
    return None  # subscript / call-chain 等复杂形式：P0 不解析


def parse_source(
    src: bytes, file_path: str, repo_id: str, language: str
) -> tuple[list[SymbolDraft], bool]:
    """解析单文件；返回 (symbols, has_error)。raw_calls 已填入 draft。"""
    parser = _get_parser(language)
    tree = parser.parse(src)
    root = tree.root_node
    drafts: list[SymbolDraft] = []

    def make(node: Node, qname: str, kind: str) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        text = src[node.start_byte : node.end_byte]
        calls: list[str] = []
        call_nodes: list[Node] = []
        _walk_calls(node, call_nodes)
        for c in call_nodes:
            t = _call_text(c)
            if t:
                calls.append(t)
        drafts.append(
            SymbolDraft(
                symbol_id=f"{repo_id}:{file_path}::{qname}",
                repo_id=repo_id,
                file_path=file_path,
                qualified_name=qname,
                kind=kind,
                content_hash=content_hash(text),
                size_bytes=len(text),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                raw_calls=sorted(set(calls)),
            )
        )

    for child in root.named_children:
        if child.type == "function_definition":
            name_node = child.child_by_field_name("name")
            if name_node is not None:
                qname = name_node.text.decode("utf-8", errors="replace")
                make(child, qname, SymbolKind.FUNCTION.value)
        elif child.type == "class_definition":
            name_node = child.child_by_field_name("name")
            if name_node is None:
                continue
            cname = name_node.text.decode("utf-8", errors="replace")
            make(child, cname, SymbolKind.CLASS.value)
            body = child.child_by_field_name("body")
            if body is None:
                continue
            for sub in body.named_children:
                if sub.type == "function_definition":
                    mname = sub.child_by_field_name("name")
                    if mname is not None:
                        m = mname.text.decode("utf-8", errors="replace")
                        make(sub, f"{cname}.{m}", SymbolKind.METHOD.value)
    return drafts, root.has_error


def resolve_dependencies(drafts: list[SymbolDraft]) -> list[dict]:
    """仓库级两趟解析：按名称消解调用边；歧义/未知记入 unresolved。"""
    by_qname: dict[str, SymbolDraft] = {}
    by_short: dict[str, list[SymbolDraft]] = {}
    for d in drafts:
        by_qname[d.qualified_name] = d
        short = d.qualified_name.rsplit(".", 1)[-1]
        by_short.setdefault(short, []).append(d)

    unresolved: list[dict] = []
    for d in sorted(drafts, key=lambda x: x.symbol_id):
        deps: set[str] = set()
        for call in d.raw_calls:
            parts = call.split(".")
            short = parts[-1]
            target: SymbolDraft | None = None
            if call in by_qname:
                target = by_qname[call]
            else:
                same_file = [
                    s
                    for s in by_short.get(short, [])
                    if s.file_path == d.file_path and s is not d
                ]
                if len(same_file) == 1:
                    target = same_file[0]
                else:
                    glob = [s for s in by_short.get(short, []) if s is not d]
                    if len(glob) == 1:
                        target = glob[0]
            if target is not None:
                if target.symbol_id != d.symbol_id:
                    deps.add(target.symbol_id)
            else:
                if short in by_short or call in by_qname:
                    unresolved.append(
                        {
                            "symbol_id": d.symbol_id,
                            "call": call,
                            "reason": "ambiguous_name",
                        }
                    )
                else:
                    unresolved.append(
                        {
                            "symbol_id": d.symbol_id,
                            "call": call,
                            "reason": "unknown_name",
                        }
                    )
        d.deps = sorted(deps)
    return unresolved


def parse_repo(root: str | Path, repo_id: str, config: AppConfig) -> ParseResult:
    """遍历仓库（确定性顺序），解析受支持语言文件并回填依赖。"""
    root = Path(root)
    result = ParseResult()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        language = config.supported_languages.get(suffix)
        if language is None:
            if suffix in UNSUPPORTED_CODE_SUFFIXES:
                result.skipped_files.append(
                    {"path": rel, "reason": "unsupported_language",
                     "suffix": suffix}
                )
            continue
        try:
            src = path.read_bytes()
        except OSError as exc:  # 读取失败明确记录，不静默
            result.parse_warnings.append(
                {"path": rel, "reason": f"read_error: {exc}"}
            )
            continue
        drafts, has_error = parse_source(src, rel, repo_id, language)
        if has_error:
            result.parse_warnings.append(
                {"path": rel, "reason": "tree_sitter_has_error"}
            )
        result.symbols.extend(drafts)

    result.unresolved_calls = resolve_dependencies(result.symbols)
    # 同一 symbol_id 出现两次（极端情况）→ 保留字典序靠前，其余记警告
    seen: set[str] = set()
    unique: list[SymbolDraft] = []
    for d in sorted(result.symbols, key=lambda x: x.symbol_id):
        if d.symbol_id in seen:
            result.parse_warnings.append(
                {"path": d.file_path, "symbol_id": d.symbol_id,
                 "reason": "duplicate_symbol_id"}
            )
            continue
        seen.add(d.symbol_id)
        unique.append(d)
    result.symbols = unique
    return result
