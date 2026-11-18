"""V13D 预览：验证锚定确定性慢层（零 LLM）。

distill：仅从调用方声明「已成功且已交付」的 workspace 抽取签名/常量。
query：按 path + 磁盘 sha 命中；sha 不一致 → None（磁盘权威）。
"""

from __future__ import annotations

import ast
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .store import content_id_of, normalize_body, pin_sha256

try:
    from v11.visibility import content_sha256 as _file_sha
except ImportError:  # pragma: no cover
    def _file_sha(text: str) -> str:
        if text:
            text = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"
        import hashlib
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class SlowUnit:
    content_id: str
    kind: str  # signature | const_contract
    body_norm: str
    pin_sha256: str
    file_path: str
    file_sha256: str  # 蒸馏时磁盘文件 hash
    origin: dict = field(default_factory=dict)
    created_at: float = 0.0


class SlowStore:
    def __init__(self, path: Path | None = None):
        self._units: dict[tuple[str, str], SlowUnit] = {}  # (path, file_sha) -> unit
        self.path = path
        if path and path.exists():
            self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for row in data:
                u = SlowUnit(**row)
                self._units[(u.file_path, u.file_sha256)] = u
        except Exception:
            pass

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = [asdict(u) for u in self._units.values()]
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    def put(self, unit: SlowUnit) -> None:
        self._units[(unit.file_path, unit.file_sha256)] = unit

    def query(self, file_path: str, disk_sha: str) -> SlowUnit | None:
        u = self._units.get((file_path, disk_sha))
        if u is None:
            return None
        if pin_sha256(u.body_norm) != u.pin_sha256:
            return None
        return u

    def __len__(self) -> int:
        return len(self._units)


def _extract(src: str) -> tuple[str, str]:
    """返回 (body, kind)。失败回退空签名。"""
    parts: list[str] = []
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return "", "signature"
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seg = ast.get_source_segment(src, node) or ""
            first = seg.splitlines()[0].rstrip() if seg else f"def {node.name}(...):"
            if not first.endswith(":"):
                first += ":"
            parts.append(first + "\n    ...\n")
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    seg = ast.get_source_segment(src, node) or ""
                    line = seg.splitlines()[0].rstrip() if seg else f"{t.id} = ..."
                    parts.append(line + "\n")
                    break
    body = "".join(parts)
    if not body:
        return "", "signature"
    try:
        ast.parse(body)
    except SyntaxError:
        return "", "signature"
    return body, "signature"


def distill_workspace(
    workspace: Path,
    store: SlowStore,
    *,
    origin: dict,
    paths: list[str] | None = None,
) -> list[SlowUnit]:
    """从 workspace 抽取；调用方保证已 eval 成功且内容已交付。"""
    out: list[SlowUnit] = []
    files = paths
    if files is None:
        files = []
        for p in sorted(workspace.rglob("*.py")):
            rel = p.relative_to(workspace).as_posix()
            if rel.startswith("eval/") or "__pycache__" in rel:
                continue
            files.append(rel)
    for rel in files:
        fp = workspace / rel
        if not fp.exists():
            continue
        try:
            raw = fp.read_text(encoding="utf-8")
        except OSError:
            continue
        body, kind = _extract(raw)
        if not body:
            continue
        body_n = normalize_body(body)
        file_sha = _file_sha(raw)
        unit = SlowUnit(
            content_id=content_id_of(body_n),
            kind=kind,
            body_norm=body_n,
            pin_sha256=pin_sha256(body_n),
            file_path=rel,
            file_sha256=file_sha,
            origin=dict(origin),
            created_at=time.time(),
        )
        store.put(unit)
        out.append(unit)
    store.save()
    return out


def file_sha_of(workspace: Path, rel: str) -> str:
    fp = workspace / rel
    raw = fp.read_text(encoding="utf-8")
    return _file_sha(raw)
