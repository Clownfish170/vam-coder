"""V1.1 可见性与 O′ 单测。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v11.visibility import (  # noqa: E402
    VisibilityTracker,
    content_sha256,
    safe_omission,
    visible_file_blocks,
)


def test_mark_from_context_and_omit_allowed():
    body = "def hot():\n    return 1\n"
    ctx = f"[ctx] v1.1\n--- FILE hot.py (full current source) ---\n{body.rstrip()}\n"
    tr = VisibilityTracker()
    tr.mark_from_context(ctx)
    sha = content_sha256(body)
    assert tr.has_visible("hot.py", sha)
    allow, reasons = safe_omission(
        relpath="hot.py",
        desired_sha=sha,
        tracker=tr,
        current_context_paths=set(),
        validity="valid",
        force_expand=False,
    )
    assert allow
    assert any("O_prime" in r for r in reasons)


def test_omit_denied_without_visibility():
    tr = VisibilityTracker()
    sha = content_sha256("def f():\n    return 0\n")
    allow, reasons = safe_omission(
        relpath="a.py",
        desired_sha=sha,
        tracker=tr,
        current_context_paths=set(),
        validity="valid",
        force_expand=False,
    )
    assert not allow
    assert "no_visible_proof_in_messages" in reasons


def test_hash_change_invalidates_visibility():
    tr = VisibilityTracker()
    ctx = "--- FILE a.py (full current source) ---\ndef f():\n    return 1\n"
    tr.mark_from_context(ctx)
    old = content_sha256("def f():\n    return 1\n")
    new = content_sha256("def f():\n    return 2\n")
    assert tr.has_visible("a.py", old)
    assert not tr.has_visible("a.py", new)


def test_assistant_marking():
    tr = VisibilityTracker()
    resp = "FILE: lib.py\n```python\ndef keep():\n    return 21\n```\n"
    tr.mark_from_assistant(resp)
    assert tr.has_visible("lib.py")
    blocks = visible_file_blocks([{"role": "assistant", "content": resp}])
    assert "lib.py" in blocks


def test_tombstone_blocks_omit():
    tr = VisibilityTracker()
    ctx = "--- FILE dead.py (full current source) ---\ndef d():\n    pass\n"
    tr.mark_from_context(ctx)
    sha = content_sha256("def d():\n    pass\n")
    allow, reasons = safe_omission(
        relpath="dead.py",
        desired_sha=sha,
        tracker=tr,
        current_context_paths=set(),
        validity="tombstoned",
        force_expand=False,
    )
    assert not allow
    assert "validity=tombstoned" in reasons
