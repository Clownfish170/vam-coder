#!/usr/bin/env python
"""Isolated workspace SHA manifest + diff validation (temp dir only)."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

OUT = Path("p1/experiments/v12_p1_readiness")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_manifest(root: Path, meta: dict) -> dict:
    files = []
    total_b = 0
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            data = p.read_bytes()
            files.append(
                {
                    "relative_path": rel,
                    "file_size": len(data),
                    "sha256": sha256_bytes(data),
                }
            )
            total_b += len(data)
    blob = json.dumps(files, sort_keys=True).encode()
    return {
        **meta,
        "timestamp": "TEST",
        "files": files,
        "total_files": len(files),
        "total_bytes": total_b,
        "manifest_sha256": sha256_bytes(blob),
    }


def diff_manifests(pre: dict, post: dict) -> dict:
    pre_m = {f["relative_path"]: f["sha256"] for f in pre["files"]}
    post_m = {f["relative_path"]: f["sha256"] for f in post["files"]}
    added = sorted(set(post_m) - set(pre_m))
    deleted = sorted(set(pre_m) - set(post_m))
    modified = sorted(
        k for k in set(pre_m) & set(post_m) if pre_m[k] != post_m[k]
    )
    unchanged = sorted(
        k for k in set(pre_m) & set(post_m) if pre_m[k] == post_m[k]
    )
    return {
        "ADDED": added,
        "MODIFIED": modified,
        "DELETED": deleted,
        "UNCHANGED": unchanged,
    }


def main() -> int:
    results = []
    with tempfile.TemporaryDirectory(prefix="ws_sha_") as td:
        ws = Path(td) / "workspace"
        ws.mkdir()
        (ws / "alpha.py").write_bytes(b"def a():\n    return 1\n")
        (ws / "beta.py").write_bytes(b"def b():\n    return 2\n")
        meta = {
            "episode_id": "TEST_EP_R1",
            "task_id": "TEST",
            "arm": "E",
            "repetition": 1,
        }
        pre = build_manifest(ws, meta)
        # modify / add / delete
        (ws / "alpha.py").write_bytes(b"def a():\n    return 10\n")
        (ws / "gamma.py").write_bytes(b"def g():\n    pass\n")
        (ws / "beta.py").unlink()
        post = build_manifest(ws, meta)
        d = diff_manifests(pre, post)

        checks = {
            "pre_has_alpha": any(f["relative_path"] == "alpha.py" for f in pre["files"]),
            "diff_ADDED_gamma": d["ADDED"] == ["gamma.py"],
            "diff_DELETED_beta": d["DELETED"] == ["beta.py"],
            "diff_MODIFIED_alpha": d["MODIFIED"] == ["alpha.py"],
            "post_recompute": build_manifest(ws, meta)["total_files"] == post["total_files"],
            "sha_alpha_post": next(
                f["sha256"]
                for f in post["files"]
                if f["relative_path"] == "alpha.py"
            )
            == sha256_bytes(b"def a():\n    return 10\n"),
        }
        post2 = build_manifest(ws, meta)
        checks["post_manifest_stable"] = post2["manifest_sha256"] == post["manifest_sha256"]

        (OUT / "workspace_sha_test_result.json").write_text(
            json.dumps(
                {"checks": checks, "diff": d, "pre_total": pre["total_files"], "post_total": post["total_files"]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(json.dumps(checks, indent=2))
        print("ALL", all(checks.values()))
        return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
