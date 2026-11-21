"""符号解析：Tree-sitter 提取函数/类/方法及依赖（当前仅支持 Python）。

语言支持边界（须与 config.supported_languages 保持一致）：
- 已支持：.py（tree-sitter-python 语法）
- 不支持：.js/.ts/.java/.go/.rs/.c/.cpp 等（本环境未安装对应 grammar），
  解析时按扩展名记入 ParseResult.skipped_files，reason=unsupported_language。
- Python 内部限制：仅提取模块级函数、类、类方法；函数内嵌套函数/嵌套类
  不作为独立符号（其调用计入外层符号）。

解析完整性——ParseResult.file_status 逐文件记录：
- success：读取成功且语法树完整 → **只有该状态**允许以本次结果更新符号
  内容依据、依赖边，并允许推断“符号缺失”（删除/重命名）；
- partial：读取成功但有语法错误 → 部分 AST **非权威**：不更新既有符号的
  哈希/依赖/版本，不 tombstone，不注册新符号（草稿仅用于诊断与名称消解）；
- failed：读取失败 → 同样不可推断；
- unsupported_language：认得出但无 grammar → 不可推断。
不在 file_status 中的受支持后缀文件 = 仓库中已不存在（真实删除/重命名）。
仓库根不存在/不是目录 → parse_repo 直接抛错，绝不把空解析当"全部删除"。
对不可推断文件中的既有符号：保留原内容依据与依赖，仅在原状态为 valid 时
保守收紧为 unverified（由 invalidation 记录原因；不允许 REUSE_KV）。

依赖消解——模块身份与 import 作用域：
1. import 分“模块级”（无函数/类祖先，含模块级 if/try 内）与“局部”
  （函数/类体内；嵌套函数计入其被索引的外层符号）；局部 import
  **只对其所在符号的调用生效，不泄漏给同文件其他函数**；
2. 调用文本与符号的对应只经由 (file_path, qualified_name) 索引，
   不使用“全局裸名限定名”任意选取；
3. 裸名解析顺序：本符号局部 import → 模块级 import（与同文件 def 冲突则
   ambiguous）→ 同文件模块级定义 → **抑制规则**（同文件其他符号对该名字
   仅有局部 import 证据 → 不可靠，unresolved）→ 全局唯一裸名（仅
   function/class）→ unresolved；
4. 属性调用：self/cls 与同文件方法、import 绑定、模块限定（mod.func）、
   类限定（Cls.method）；未知对象属性只允许同文件唯一匹配；
5. 任何无法消歧的调用记入 unresolved_calls（含 detail 原因），不建猜测边。
Python-only；不做完整 Python 作用域/绑定时序语义（见 README 已知限制）。
"""

from __future__ import annotations

import re
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
             ".playwright-cli", ".pytest_cache", ".backup"}

# 逐文件解析状态
# success：读取成功且语法树完整；partial：读取成功但有语法错误（部分 AST，
# 非权威）；failed：读取失败；unsupported_language：认得出但无 grammar。
# 错误细节保留在 ParseResult.file_errors / parse_warnings。
STATUS_SUCCESS = "success"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"
STATUS_UNSUPPORTED = "unsupported_language"

# 允许以本次解析结果更新记忆/推断“符号缺失”的唯一状态
CONFIRMED_STATUSES = {STATUS_SUCCESS}

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
    # 受支持后缀文件 → 解析状态（缺失的文件见模块 docstring）
    file_status: dict[str, str] = field(default_factory=dict)
    file_errors: dict[str, str] = field(default_factory=dict)
    # 文件相对路径 → {本地名: import 绑定}
    import_bindings: dict[str, dict[str, dict]] = field(default_factory=dict)


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


# ---------------------------------------------------------------------------
# import 绑定与模块身份
# ---------------------------------------------------------------------------

def _node_text(node: Node) -> str:
    text = node.text
    if isinstance(text, bytes):
        return text.decode("utf-8", errors="replace")
    return ""


def _split_import_items(body: str) -> list[tuple[str, str | None]]:
    """'a, b as c' → [('a', None), ('b', 'c')]；容忍括号换行写法。"""
    body = body.replace("(", " ").replace(")", " ")
    items: list[tuple[str, str | None]] = []
    for raw in body.split(","):
        raw = raw.strip()
        if not raw:
            continue
        m = re.match(r"^(\S+)\s+as\s+(\S+)$", raw)
        if m:
            items.append((m.group(1), m.group(2)))
        else:
            items.append((raw, None))
    return items


def _module_of_file(file_path: str) -> str | None:
    """"core.py"→"core"；"pkg/mod.py"→"pkg.mod"；"pkg/__init__.py"→"pkg"。"""
    if not file_path.endswith(".py"):
        return None
    stem = file_path[: -len(".py")]
    if stem == "__init__":
        return None
    if stem.endswith("/__init__"):
        stem = stem[: -len("/__init__")]
    return stem.replace("/", ".") or None


def _resolve_relative(file_path: str, level: int, module: str) -> str | None:
    """相对导入（from . / from ..）→ 绝对模块名；越出根则无法确认。"""
    parts = file_path.split("/")
    dirs = parts[:-1]
    keep = len(dirs) - max(level - 1, 0)
    if keep < 0:
        return None
    base = dirs[:keep]
    if module:
        return ".".join(base + [module]) if base else module
    return ".".join(base) if base else None


def _ancestors(node: Node) -> list[Node]:
    out: list[Node] = []
    cur = node.parent
    while cur is not None:
        out.append(cur)
        cur = cur.parent
    return out


def _indexed_symbol_qname(node: Node) -> str | None:
    """function/class 节点若会被 parse_source 索引，返回其限定名；否则 None。

    规则与 parse_source 对齐：模块级函数/类；模块级类的方法。
    嵌套函数/嵌套类等不被索引 → None。
    """
    if node.type == "class_definition":
        if any(
            a.type in ("function_definition", "class_definition")
            for a in _ancestors(node)
        ):
            return None
        name = node.child_by_field_name("name")
        return _node_text(name) if name else None
    if node.type == "function_definition":
        sym_anc = [
            a for a in _ancestors(node)
            if a.type in ("function_definition", "class_definition")
        ]
        if not sym_anc:
            name = node.child_by_field_name("name")
            return _node_text(name) if name else None
        if len(sym_anc) == 1 and sym_anc[0].type == "class_definition":
            cls_q = _indexed_symbol_qname(sym_anc[0])
            if cls_q is None:
                return None
            mname = node.child_by_field_name("name")
            return f"{cls_q}.{_node_text(mname)}" if mname else None
        return None  # 嵌套函数（含方法内嵌套）
    return None


def _enclosing_indexed_qname(node: Node) -> str | None:
    """导入语句 → 所属被索引符号的限定名；模块级 → None。"""
    cur = node.parent
    while cur is not None:
        if cur.type in ("function_definition", "class_definition"):
            q = _indexed_symbol_qname(cur)
            if q is not None:
                return q
        cur = cur.parent
    return None


def _merge_binds(scope: dict[str, dict], new_binds: dict[str, dict]) -> None:
    """同作用域合并绑定（P0.3 任务 2）：同名不同目标 → 记 conflict 歧义，
    绝不按树遍历顺序任选其一；同名同目标（重复 import 同一来源）幂等保留。"""
    for key, bind in new_binds.items():
        prev = scope.get(key)
        if prev is None:
            scope[key] = dict(bind)
        elif prev.get("kind") == "conflict":
            if bind not in prev["targets"]:
                prev["targets"].append(bind)
        elif prev == bind:
            continue  # 同目标重复 → 非冲突
        else:
            scope[key] = {"kind": "conflict", "targets": [prev, bind]}


def extract_import_bindings(
    src: bytes, file_path: str, language: str = "python"
) -> dict:
    """提取 import 语句并按作用域分层（任务 2 + P0.3 冲突检查）。

    返回 {"module": {本地名: 绑定}, "local": {符号限定名: {本地名: 绑定}}}。
    - module：模块级 import（无函数/类祖先，含模块级 if/try 内）；
    - local：函数/类体内的局部 import，只归属该符号（嵌套函数计入外层）。
    同作用域同名出现不同目标 → 绑定记为 kind=conflict（消解时
    unresolved，不按遍历顺序任选）。作用域为文件级近似：不分析绑定
    执行顺序与条件分支可达性。
    """
    if language != "python":
        return {"module": {}, "local": {}}
    parser = _get_parser(language)
    tree = parser.parse(src)
    module_bindings: dict[str, dict] = {}
    local_by_symbol: dict[str, dict[str, dict]] = {}
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        text = _node_text(node)
        binds: dict[str, dict] = {}
        if node.type == "import_statement":
            body = text[len("import"):].strip()
            for orig, alias in _split_import_items(body):
                dotted = orig.lstrip(".").strip()
                if not dotted:
                    continue
                if alias:
                    # import a.b as x → x 指向模块 a.b
                    binds[alias] = {"kind": "module", "module": dotted}
                else:
                    # import a.b → 绑定顶层名 a（模块身份取 a）
                    head = dotted.split(".")[0]
                    binds[head] = {"kind": "module", "module": head}
        elif node.type == "import_from_statement":
            m = re.match(r"from\s+([.\w]+)\s+import\s+(.*)\Z", text, re.DOTALL)
            if not m:
                continue
            module_part, names_part = m.group(1), m.group(2)
            level = len(module_part) - len(module_part.lstrip("."))
            mod_name = module_part.lstrip(".")
            base = _resolve_relative(file_path, level, mod_name)
            if base is None:
                continue  # 相对导入越出仓库根 → 无法确认，不建绑定
            for orig, alias in _split_import_items(names_part):
                if orig == "*":
                    # wildcard：无法逐名消解，只记录（不用于建边）
                    binds.setdefault("*", {"kind": "wildcard", "module": base})
                    continue
                local = alias or orig
                binds[local] = {
                    "kind": "symbol", "module": base, "name": orig
                }
        if not binds:
            continue
        owner = _enclosing_indexed_qname(node)
        if owner is None:
            _merge_binds(module_bindings, binds)
        else:
            _merge_binds(local_by_symbol.setdefault(owner, {}), binds)
    return {"module": module_bindings, "local": local_by_symbol}


class _RepoIndex:
    """仓库级符号/模块索引：所有解析只经 (file_path, qualified_name) 查询。

    **可信目标边界（P0.3 任务 1）**：调用方必须只传入 success 文件的符号
    （parse_repo 过滤）——partial/failed/unsupported 的部分 AST 符号仅供
    诊断，不作为正式依赖目标；import 绑定与全局回退均经此索引，因此同样
    被隔离。
    """

    def __init__(self, symbols, import_bindings: dict[str, dict]):
        self.import_bindings = import_bindings
        self.by_fq: dict[tuple[str, str], object] = {}
        self.by_file_short: dict[str, dict[str, list]] = {}
        self.by_short_top: dict[str, list] = {}  # 仅 function/class（裸名全局回退）
        self.module_to_files: dict[str, list[str]] = {}
        for s in symbols:
            self.by_fq[(s.file_path, s.qualified_name)] = s
            short = s.qualified_name.rsplit(".", 1)[-1]
            self.by_file_short.setdefault(s.file_path, {}) \
                .setdefault(short, []).append(s)
            if s.kind in (SymbolKind.FUNCTION.value, SymbolKind.CLASS.value):
                self.by_short_top.setdefault(short, []).append(s)
            mod = _module_of_file(s.file_path)
            # 同文件多符号只登记一次文件（去重，避免误判模块歧义）
            if mod and s.file_path not in self.module_to_files.setdefault(mod, []):
                self.module_to_files[mod].append(s.file_path)
        for files in self.module_to_files.values():
            files.sort()

    def module_file(self, module: str) -> str | None:
        """模块 → 唯一文件；歧义（pkg.py 与 pkg/__init__.py 并存）→ None。"""
        files = self.module_to_files.get(module, [])
        return files[0] if len(files) == 1 else None

    def same_file(self, file_path: str, short: str, exclude) -> list:
        return [
            s for s in self.by_file_short.get(file_path, {}).get(short, [])
            if s is not exclude
        ]


def _resolve_binding(
    bind: dict, index: _RepoIndex
) -> tuple[str, object] | tuple[str, str, str] | None:
    """import 绑定 → ('symbol', file, qname) | ('module', file) | None。"""
    if bind.get("kind") == "module":
        f = index.module_file(bind["module"])
        return ("module", f) if f else None
    if bind.get("kind") == "symbol":
        files = index.module_to_files.get(bind["module"], [])
        if len(files) != 1:
            return None
        f = files[0]
        if (f, bind["name"]) in index.by_fq:
            return ("symbol", f, bind["name"])
        # from pkg import sub → 可能是子模块
        sub = f"{bind['module']}.{bind['name']}"
        sub_f = index.module_file(sub)
        if sub_f:
            return ("module", sub_f)
    return None


def _file_scope_bindings(
    d: SymbolDraft, index: "_RepoIndex"
) -> tuple[dict, dict, set[str]]:
    """该符号的有效作用域：局部 import（本符号）+ 模块级 + 他符号局部名集合。"""
    file_imp = index.import_bindings.get(d.file_path) or {}
    module_bindings = file_imp.get("module", {}) or {}
    local_bindings = (
        file_imp.get("local", {}) or {}
    ).get(d.qualified_name, {}) or {}
    other_local_keys = {
        k
        for sym, binds in (file_imp.get("local", {}) or {}).items()
        if sym != d.qualified_name
        for k in binds
    }
    return module_bindings, local_bindings, other_local_keys


def _resolve_call(
    d: SymbolDraft, call: str, index: "_RepoIndex"
) -> tuple[object | None, str | None, str | None]:
    """返回 (目标符号|None, 未消解原因|None, detail|None)。不猜测。"""
    module_bindings, local_bindings, other_local_keys = _file_scope_bindings(
        d, index
    )
    parts = call.split(".")

    if len(parts) == 1:
        name = parts[0]
        same = index.same_file(d.file_path, name, d)
        # 1) 本符号的局部 import（任务 2：不泄漏给其他函数）
        local_bind = local_bindings.get(name)
        if local_bind is not None:
            if local_bind.get("kind") == "conflict":
                return None, "ambiguous_name", (
                    "conflicting imports in same (local) scope: "
                    f"{local_bind.get('targets')} — final binding "
                    "undecidable"
                )
            resolved = _resolve_binding(local_bind, index)
            if resolved and resolved[0] == "symbol":
                return index.by_fq[(resolved[1], resolved[2])], None, None
            return None, "unknown_name", "local import target not in repo"
        # 2) 模块级 import（与同文件 def 冲突 → 绑定顺序未知）
        bind = module_bindings.get(name)
        if bind is not None:
            if bind.get("kind") == "conflict":
                return None, "ambiguous_name", (
                    "conflicting imports in same (module) scope: "
                    f"{bind.get('targets')} — final binding undecidable"
                )
            if bind.get("kind") == "wildcard":
                return None, "unknown_name", "wildcard import is not resolved"
            if same:
                return None, "ambiguous_name", (
                    "module-level import conflicts with same-file definition "
                    "(binding order unanalyzed)"
                )
            resolved = _resolve_binding(bind, index)
            if resolved and resolved[0] == "symbol":
                return index.by_fq[(resolved[1], resolved[2])], None, None
            return None, "unknown_name", "import target not in repo"
        # 3) 同文件模块级定义（唯一匹配）
        if len(same) == 1:
            return same[0], None, None
        if len(same) > 1:
            return None, "ambiguous_name", "multiple same-file candidates"
        # 4) 抑制规则：同文件其他符号仅有局部 import 证据 → 不可靠
        if name in other_local_keys:
            return None, "ambiguous_name", (
                "name is function-local imported in another scope "
                "(local import must not leak); module-level binding "
                "unconfirmed"
            )
        # 5) 全局唯一裸名（仅 function/class；只在 success 可信目标中查）
        glob = [
            s for s in index.by_short_top.get(name, [])
            if s.symbol_id != d.symbol_id
        ]
        if len(glob) == 1:
            return glob[0], None, None
        if len(glob) > 1:
            return None, "ambiguous_name", "multiple repo-wide candidates"
        return None, "unknown_name", (
            "no trusted candidate among success-parsed symbols "
            "(targets from partial/failed files are excluded)"
        )

    # ---- attribute 调用 ----
    head, rest = parts[0], ".".join(parts[1:])
    short = parts[-1]

    if head in ("self", "cls"):
        same = index.same_file(d.file_path, short, d)
        if len(same) == 1:
            return same[0], None, None
        if len(same) > 1:
            return None, "ambiguous_name", None
        return None, "unknown_name", None

    bind = local_bindings.get(head) or module_bindings.get(head)
    if bind is not None:
        if bind.get("kind") == "conflict":
            return None, "ambiguous_name", (
                f"conflicting imports in same scope for {head!r}: "
                f"{bind.get('targets')} — final binding undecidable"
            )
        resolved = _resolve_binding(bind, index)
        if resolved is None:
            return None, "unknown_name", "import target not in repo"
        if resolved[0] == "module":
            f = resolved[1]
            tgt = index.by_fq.get((f, rest))
            if tgt is not None:
                return tgt, None, None
            return None, "unknown_name", None
        # 符号上的属性：如 imported Class.method
        _, f, name = resolved
        tgt = index.by_fq.get((f, f"{name}.{rest}"))
        if tgt is not None:
            return tgt, None, None
        tgt = index.by_fq.get((f, rest))
        if tgt is not None:
            return tgt, None, None
        return None, "unknown_name", None

    # 模块限定调用（mod.func）：mod 为仓库唯一模块（显式模块身份，可靠）
    f = index.module_file(head)
    if f is not None:
        tgt = index.by_fq.get((f, rest))
        if tgt is not None:
            return tgt, None, None
        return None, "unknown_name", None

    # 类限定调用（Cls.method）：同文件类优先，其次全局唯一类
    cls_same = [
        s for s in index.same_file(d.file_path, head, d)
        if s.kind == SymbolKind.CLASS.value
    ]
    cls_glob = [
        s for s in index.by_short_top.get(head, [])
        if s.kind == SymbolKind.CLASS.value
    ]
    cls_candidates = cls_same if cls_same else cls_glob
    if len(cls_candidates) == 1:
        cp = cls_candidates[0].file_path
        tgt = index.by_fq.get((cp, f"{head}.{rest}"))
        if tgt is not None:
            return tgt, None, None
        return None, "unknown_name", None
    if len(cls_candidates) > 1:
        return None, "ambiguous_name", None

    # 未知对象的属性：仅同文件唯一匹配（跨文件猜测一律拒绝）
    same = index.same_file(d.file_path, short, d)
    if len(same) == 1:
        return same[0], None, None
    if len(same) > 1:
        return None, "ambiguous_name", None
    return None, "unknown_name", None


def resolve_dependencies(
    drafts: list[SymbolDraft],
    index_symbols,
    import_bindings: dict[str, dict] | None = None,
) -> list[dict]:
    """按调用文本消解依赖边；歧义/未知记入 unresolved（含 detail），不建猜测边。

    drafts：需要回填 deps 的符号（raw_calls 已解析）；
    index_symbols：作为查询域的全部符号（含 drafts 或库中已有符号）；
    import_bindings：{file_path: {"module": …, "local": …}}（作用域分层，
    见 extract_import_bindings）。
    """
    index = _RepoIndex(list(index_symbols), import_bindings or {})
    unresolved: list[dict] = []
    for d in sorted(drafts, key=lambda x: x.symbol_id):
        deps: set[str] = set()
        for call in d.raw_calls:
            target, reason, detail = _resolve_call(d, call, index)
            if target is not None:
                if target.symbol_id != d.symbol_id:
                    deps.add(target.symbol_id)
            else:
                record: dict = {
                    "symbol_id": d.symbol_id,
                    "call": call,
                    "reason": reason or "unknown_name",
                }
                if detail:
                    record["detail"] = detail
                unresolved.append(record)
        d.deps = sorted(deps)
    return unresolved


# ---------------------------------------------------------------------------


def parse_repo(root: str | Path, repo_id: str, config: AppConfig) -> ParseResult:
    """遍历仓库（确定性顺序），解析受支持语言文件并回填依赖。

    仓库根不存在/不是目录 → 抛 FileNotFoundError/NotADirectoryError
    。
    """
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"repo root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"repo root is not a directory: {root}")
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
                result.file_status[rel] = STATUS_UNSUPPORTED
                result.skipped_files.append(
                    {"path": rel, "reason": "unsupported_language",
                     "suffix": suffix}
                )
            continue
        try:
            src = path.read_bytes()
        except OSError as exc:  # 读取失败明确记录，不静默、不推断删除
            reason = f"read_error: {exc}"
            result.file_status[rel] = STATUS_FAILED
            result.file_errors[rel] = reason
            result.parse_warnings.append({"path": rel, "reason": reason})
            continue
        drafts, has_error = parse_source(src, rel, repo_id, language)
        if has_error:
            result.file_status[rel] = STATUS_PARTIAL
            result.file_errors[rel] = "tree_sitter_has_error"
            result.parse_warnings.append(
                {"path": rel, "reason": "tree_sitter_has_error"}
            )
        else:
            result.file_status[rel] = STATUS_SUCCESS
        result.symbols.extend(drafts)
        result.import_bindings[rel] = extract_import_bindings(src, rel, language)

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

    # P0.3 任务 1：可信依赖目标 = success 文件的完整解析符号；
    # partial/failed/unsupported 的符号保留在 result.symbols（诊断），
    # 但不进入解析索引 → 不会成为正式依赖边的目标（含 import 绑定与
    # 全局唯一裸名回退）；无法消歧 → unresolved_calls（含 detail）。
    trusted_targets = [
        d for d in unique
        if result.file_status.get(d.file_path) == STATUS_SUCCESS
    ]
    result.unresolved_calls = resolve_dependencies(
        unique, trusted_targets, result.import_bindings
    )
    return result
