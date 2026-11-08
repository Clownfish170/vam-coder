"""P1 workspace pre/post/diff manifests (byte-level SHA256)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_workspace_manifest(root: Path, meta: dict) -> dict:
    """Hash all files under root (relative paths)."""
    files = []
    total = 0
    if root.exists():
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                data = p.read_bytes()
                files.append(
                    {
                        "relative_path": rel,
                        "file_size": len(data),
                        "sha256": _sha(data),
                    }
                )
                total += len(data)
    blob = json.dumps(files, sort_keys=True).encode()
    return {
        **meta,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root),
        "files": files,
        "total_files": len(files),
        "total_bytes": total,
        "manifest_sha256": _sha(blob),
    }


def workspace_diff(pre: dict, post: dict) -> dict:
    pm = {f["relative_path"]: f["sha256"] for f in pre.get("files", [])}
    qm = {f["relative_path"]: f["sha256"] for f in post.get("files", [])}
    return {
        "ADDED": sorted(set(qm) - set(pm)),
        "DELETED": sorted(set(pm) - set(qm)),
        "MODIFIED": sorted(k for k in set(pm) & set(qm) if pm[k] != qm[k]),
        "UNCHANGED": sorted(k for k in set(pm) & set(qm) if pm[k] == qm[k]),
    }


def write_episode_workspace_evidence(
    *,
    source_project: Path,
    workspace: Path,
    episode_dir: Path,
    episode_id: str,
    task_id: str,
    arm: str,
    repetition: int,
) -> dict:
    """Write pre (from frozen source), post (from live workspace), and diff.

    pre is taken from the frozen task project **before** the runner mutates
    the episode workspace (caller must invoke prior to model execution).
    post is taken after the episode completes.
    """
    meta = {
        "episode_id": episode_id,
        "task_id": task_id,
        "arm": arm,
        "repetition": repetition,
    }
    episode_dir.mkdir(parents=True, exist_ok=True)
    pre = build_workspace_manifest(source_project, meta)
    (episode_dir / "workspace_pre_manifest.json").write_text(
        json.dumps(pre, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Caller may call write_pre and write_post separately around the run.
    return pre


def write_post_and_diff(
    *,
    workspace: Path,
    episode_dir: Path,
    episode_id: str,
    task_id: str,
    arm: str,
    repetition: int,
) -> dict:
    meta = {
        "episode_id": episode_id,
        "task_id": task_id,
        "arm": arm,
        "repetition": repetition,
    }
    pre_p = episode_dir / "workspace_pre_manifest.json"
    if not pre_p.exists():
        raise FileNotFoundError(f"missing pre manifest: {pre_p}")
    pre = json.loads(pre_p.read_text(encoding="utf-8"))
    post = build_workspace_manifest(workspace, meta)
    diff = workspace_diff(pre, post)
    (episode_dir / "workspace_post_manifest.json").write_text(
        json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (episode_dir / "workspace_diff.json").write_text(
        json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"pre_files": pre["total_files"], "post_files": post["total_files"], "diff": diff}
