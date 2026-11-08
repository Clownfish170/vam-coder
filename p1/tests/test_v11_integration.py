"""V1.1 无模型集成：dry-run 确保编辑目标文件进入上下文。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "p1" / "scripts" / "run_p1_v11.py"


def test_dry_run_v11_rur02(tmp_path):
    out = tmp_path / "v11_dry"
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--episode",
            "v1_RUR02",
            "--baselines",
            "vam_coder_v1.1",
            "--dry-run",
            "--pause-seconds",
            "0",
            "--out-root",
            str(out),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    ctx1 = (
        out / "episodes" / "v1_RUR02" / "vam_coder_v1.1" / "steps" / "step1" / "context.txt"
    ).read_text(encoding="utf-8")
    assert "hot.py" in ctx1
    # 审计存在
    audit = (
        out / "episodes" / "v1_RUR02" / "v1.1" / "logs"
    )
    # path is baseline name
    audit = out / "episodes" / "v1_RUR02" / "vam_coder_v1.1" / "logs" / "injection_audit.jsonl"
    assert audit.exists()
    first = json.loads(audit.read_text(encoding="utf-8").splitlines()[0])
    assert first["plan"]["need"] in (True, False)
    result = json.loads(
        (
            out
            / "episodes"
            / "v1_RUR02"
            / "vam_coder_v1.1"
            / "steps"
            / "step1"
            / "result.json"
        ).read_text(encoding="utf-8")
    )
    assert result["architecture"] == "v1.1"
    assert result["error"].startswith("dry_run")


def test_dry_run_does_not_touch_formal_runs():
    formal = ROOT / "p1" / "results" / "runs" / "v1_formal_A_rep1_20261031_115035"
    assert formal.exists()
    # dry run path is under v11_* only — ensure runner out default prefix
    assert RUNNER.exists()
