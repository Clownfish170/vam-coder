"""测试夹具：临时仓库 + 临时库/日志（不触碰项目 state/logs 实际文件）。"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from vam_coder.config import AppConfig
from vam_coder.logging_util import JsonlLogger
from vam_coder.store import StaticStore

REPO_V1 = {
    "core.py": (
        '"""Core helpers."""\n'
        "\n"
        "\n"
        "def compute(x):\n"
        '    """Compute doubled value."""\n'
        "    return x * 2\n"
        "\n"
        "\n"
        "def helper(x):\n"
        "    return compute(x) + 1\n"
    ),
    "app.py": (
        "def run(x):\n"
        "    return helper(x)\n"
        "\n"
        "\n"
        "def lone():\n"
        "    return 42\n"
    ),
}

# v2：compute 内容变化（helper 调用它，run 调用 helper → 闭包 d=1,2）
REPO_V2_COMPUTE_CHANGED = {
    "core.py": (
        '"""Core helpers."""\n'
        "\n"
        "\n"
        "def compute(x):\n"
        '    """Compute tripled value."""\n'
        "    return x * 3\n"
        "\n"
        "\n"
        "def helper(x):\n"
        "    return compute(x) + 1\n"
    ),
    "app.py": REPO_V1["app.py"],
}

# v2'：compute 重命名为 calc
REPO_V2_RENAMED = {
    "core.py": (
        '"""Core helpers."""\n'
        "\n"
        "\n"
        "def calc(x):\n"
        '    """Compute doubled value."""\n'
        "    return x * 2\n"
        "\n"
        "\n"
        "def helper(x):\n"
        "    return compute(x) + 1\n"
    ),
    "app.py": REPO_V1["app.py"],
}

# v2''：删除 lone
REPO_V2_LONE_DELETED = {
    "core.py": REPO_V1["core.py"],
    "app.py": (
        "def run(x):\n"
        "    return helper(x)\n"
    ),
}


def write_repo(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def sid(repo_id: str, file_path: str, qname: str) -> str:
    return f"{repo_id}:{file_path}::{qname}"


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        db_path=str(tmp_path / "store.db"),
        decision_log=str(tmp_path / "decisions.jsonl"),
        invalidation_log=str(tmp_path / "invalidation_events.jsonl"),
        budget_tokens=4096,
        closure_depth=2,
    )


@pytest.fixture
def store(config: AppConfig):
    s = StaticStore(config.db_path)
    yield s
    s.close()


@pytest.fixture
def logger(config: AppConfig) -> JsonlLogger:
    return JsonlLogger(config.invalidation_log)


@pytest.fixture
def repo_v1(tmp_path: Path) -> Path:
    return write_repo(tmp_path / "repo", dict(REPO_V1))


@pytest.fixture
def fresh_repo(tmp_path: Path):
    """返回一个写入函数，便于测试中途换版本内容。"""
    root = tmp_path / "repo"

    def _write(files: dict[str, str]) -> Path:
        # 清掉旧文件，保证“删除”场景干净
        if root.exists():
            shutil.rmtree(root)
        return write_repo(root, files)

    _write(REPO_V1)
    return _write
