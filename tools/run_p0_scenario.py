"""P0 场景实验：在构造的“API 变更”用例上验证失效与路由（报告 §6 P0 验收）。

运行（项目根目录）：
    python tools/run_p0_scenario.py

输出：
    logs/scenario_decisions.jsonl      路由决策日志（逐条决策含理由）
    logs/scenario_invalidation.jsonl   失效事件日志（逐次失效含原因）
    results/p03_scenario_report.json   六项必过检查的逐条结果 + 环境信息
        （P0.3 起改用带版本标识的文件名，避免覆盖 Git 基线中的
        results/p0_scenario_report.json —— 该原始版本已归档至
        results/archive_git_37bf61c/）
退出码：0 = 六项全过；1 = 有失败（不修饰结果）。
"""

from __future__ import annotations

import importlib.metadata as md
import json
import platform
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vam_coder.config import AppConfig  # noqa: E402
from vam_coder.invalidation import InvalidationManager  # noqa: E402
from vam_coder.logging_util import JsonlLogger  # noqa: E402
from vam_coder.models import Action, RouteRequest, Validity  # noqa: E402
from vam_coder.pipeline import route_repo  # noqa: E402
from vam_coder.router import RuleRouter  # noqa: E402
from vam_coder.store import StaticStore  # noqa: E402

CORE_V1 = (
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
)
CORE_V2_CHANGED = (
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
)
CORE_V2_RENAMED = (
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
)
APP_V1 = (
    "def run(x):\n"
    "    return helper(x)\n"
    "\n"
    "\n"
    "def lone():\n"
    "    return 42\n"
)
APP_V2_DELETED = (
    "def run(x):\n"
    "    return helper(x)\n"
)


def sid(file_path: str, qname: str) -> str:
    return f"scenario:{file_path}::{qname}"


def write_repo(root: Path, files: dict[str, str]) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for rel, text in files.items():
        (root / rel).write_text(text, encoding="utf-8")


def validity(store: StaticStore, symbol_id: str) -> str | None:
    entry = store.get(symbol_id)
    return entry.validity if entry else None


def main() -> int:
    # ---- 环境与路径（本脚本专属产物，可重复运行）----
    scenario_repo = PROJECT_ROOT / "state" / "scenario_repo"
    decision_log = PROJECT_ROOT / "logs" / "scenario_decisions.jsonl"
    invalid_log = PROJECT_ROOT / "logs" / "scenario_invalidation.jsonl"
    report_path = PROJECT_ROOT / "results" / "p03_scenario_report.json"
    db_path = PROJECT_ROOT / "state" / "scenario_store.db"
    for p in (decision_log, invalid_log, db_path):
        if p.exists():
            p.unlink()

    cfg = AppConfig.load(PROJECT_ROOT / "config" / "default.json")
    cfg.db_path = str(db_path)
    cfg.decision_log = str(decision_log)
    cfg.invalidation_log = str(invalid_log)
    dlog = JsonlLogger(decision_log)
    ilog = JsonlLogger(invalid_log)

    checks: list[dict] = []

    def record(cid: str, name: str, passed: bool, detail: str) -> None:
        checks.append(
            {"id": cid, "name": name, "passed": bool(passed), "detail": detail}
        )

    store = StaticStore(db_path)
    try:
        mgr = InvalidationManager(store, cfg, ilog)

        # ============ C1 源码未变化 → 哈希与版本状态保持一致 ============
        write_repo(scenario_repo, {"core.py": CORE_V1, "app.py": APP_V1})
        out1 = mgr.sync(scenario_repo, "scenario")
        snap1 = {
            k: (v.version, v.content_hash, v.source_hash, v.validity)
            for k, v in store.list_symbols("scenario").items()
        }
        ver1 = store.get_repo_version("scenario")
        out2 = mgr.sync(scenario_repo, "scenario")
        snap2 = {
            k: (v.version, v.content_hash, v.source_hash, v.validity)
            for k, v in store.list_symbols("scenario").items()
        }
        c1_ok = (
            len(out1.inserted) == 4
            and not out2.mutated
            and out2.unchanged_count == 4
            and ver1 == out2.repo_version_after
            and snap1 == snap2
        )
        record("C1", "源码未变化时哈希和版本状态保持一致", c1_ok,
               f"inserted={len(out1.inserted)}, repo_version={ver1} → "
               f"{out2.repo_version_after}, unchanged={out2.unchanged_count}, "
               f"snapshot_equal={snap1 == snap2}")

        # ============ C2 函数内容变化 → 旧记忆失效 ============
        write_repo(scenario_repo, {"core.py": CORE_V2_CHANGED, "app.py": APP_V1})
        out3 = mgr.sync(scenario_repo, "scenario")
        compute = store.get(sid("core.py", "compute"))
        c2_ok = (
            sid("core.py", "compute") in out3.content_changed
            and compute.validity == Validity.STALE.value
            and compute.version == 2
        )
        record("C2", "函数内容变化时旧记忆失效", c2_ok,
               f"compute validity={compute.validity}, version={compute.version}")

        # ============ C3 依赖变化 → 依赖方 unverified（深度≤2）============
        helper_v = validity(store, sid("core.py", "helper"))
        run_v = validity(store, sid("app.py", "run"))
        lone_v = validity(store, sid("app.py", "lone"))
        helper = store.get(sid("core.py", "helper"))
        c3_ok = (
            helper_v == Validity.UNVERIFIED.value
            and run_v == Validity.UNVERIFIED.value
            and lone_v == Validity.VALID.value
            and helper.version == 1  # 自身未改：版本不 bump
        )
        record("C3", "依赖函数变化时相关依赖方按规则进入 unverified", c3_ok,
               f"helper(d1)={helper_v}, run(d2)={run_v}, lone={lone_v}, "
               f"helper.version={helper.version}")

        # ============ C4 删除 / 重命名 → tombstone ============
        write_repo(scenario_repo, {"core.py": CORE_V1, "app.py": APP_V2_DELETED})
        mgr.sync(scenario_repo, "scenario")
        deleted_v = validity(store, sid("app.py", "lone"))
        write_repo(scenario_repo, {"core.py": CORE_V2_RENAMED, "app.py": APP_V1})
        out4 = mgr.sync(scenario_repo, "scenario")
        old_v = validity(store, sid("core.py", "compute"))
        new_v = validity(store, sid("core.py", "calc"))
        c4_ok = (
            deleted_v == Validity.TOMBSTONED.value
            and sid("core.py", "compute") in out4.tombstoned
            and old_v == Validity.TOMBSTONED.value
            and new_v == Validity.VALID.value
        )
        record("C4", "函数删除或重命名时旧符号不能被当作有效对象", c4_ok,
               f"lone(删除后)={deleted_v}, compute(旧名)={old_v}, "
               f"calc(新名)={new_v}")

        # ---- 复位到干净的 v1 状态（重出现即复活 + 显式 verify 恢复协议）----
        write_repo(scenario_repo, {"core.py": CORE_V1, "app.py": APP_V1})
        mgr.sync(scenario_repo, "scenario")
        v_helper = mgr.verify(sid("core.py", "helper"), scenario_repo)
        v_run = mgr.verify(sid("app.py", "run"), scenario_repo)

        # ============ C5 失效记忆不能 REUSE_KV ============
        write_repo(scenario_repo, {"core.py": CORE_V2_CHANGED, "app.py": APP_V1})
        mgr.sync(scenario_repo, "scenario")
        r_invalid = route_repo(store, "scenario", cfg, logger=dlog,
                               request_meta={"case": "C5-invalid"})
        act = r_invalid.actions()
        stale_action = act.get(sid("core.py", "compute"))
        unver_action = act.get(sid("core.py", "helper"))
        run_action = act.get(sid("app.py", "run"))
        # 单独路由仍留在库中的 tombstoned 条目（calc 于重命名阶段被墓碑化）
        tomb_entry = store.get(sid("core.py", "calc"))
        tomb_actions = RuleRouter(cfg, dlog).route(
            RouteRequest(entries=[tomb_entry],
                         request_meta={"case": "C5-tombstone"})
        ).actions()
        c5_ok = (
            stale_action == Action.EXPAND.value
            and unver_action == Action.EXPAND.value
            and run_action == Action.EXPAND.value
            and Action.REUSE_KV.value
            not in (stale_action, unver_action, run_action)
            and tomb_actions.get(sid("core.py", "calc")) == Action.DROP.value
            and act.get(sid("app.py", "lone")) == Action.REUSE_KV.value
        )
        record("C5", "失效记忆不能执行 REUSE_KV", c5_ok,
               f"compute(stale)={stale_action}, helper(unverified)="
               f"{unver_action}, run(unverified)={run_action}, "
               f"calc(tombstoned)={tomb_actions.get(sid('core.py', 'calc'))}, "
               f"lone(valid,对照)={act.get(sid('app.py', 'lone'))}")

        # ============ C6 可复现 + 日志可解释 ============
        r_a = route_repo(store, "scenario", cfg, logger=dlog,
                         request_meta={"case": "C6-a"})
        r_b = route_repo(store, "scenario", cfg, logger=dlog,
                         request_meta={"case": "C6-b"})
        route_events = [e for e in JsonlLogger.read_all(decision_log)
                        if e["event"] == "route"]
        all_reasons = all(
            d["reasons"] for ev in route_events for d in ev["decisions"]
        )
        invalid_events = JsonlLogger.read_all(invalid_log)
        c6_ok = (
            r_a.request_id == r_b.request_id
            and r_a.actions() == r_b.actions()
            and all_reasons
            and len(route_events) >= 3
            and any(e["event"] == "content_stale" for e in invalid_events)
            and any(e["event"] == "dependent_unverified"
                    for e in invalid_events)
            and any(e["event"] == "tombstone" for e in invalid_events)
        )
        record("C6", "重复执行相同输入时结果可复现，日志能解释路由决策",
               c6_ok,
               f"request_id {r_a.request_id} == {r_b.request_id} → "
               f"{r_a.request_id == r_b.request_id}; route_events="
               f"{len(route_events)}; all_decisions_have_reasons="
               f"{all_reasons}; verify恢复 helper={v_helper}, run={v_run}")
    finally:
        store.close()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "env": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "tree_sitter": md.version("tree-sitter"),
            "tree_sitter_python": md.version("tree-sitter-python"),
            "blake3": md.version("blake3"),
            "pytest": md.version("pytest"),
            "sqlite": sqlite3.sqlite_version,
        },
        "config": cfg.routing_dict(),
        "logs": {
            "decisions": str(decision_log.relative_to(PROJECT_ROOT)),
            "invalidation": str(invalid_log.relative_to(PROJECT_ROOT)),
        },
        "checks": checks,
        "passed": all(c["passed"] for c in checks),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"P0 scenario report -> {report_path}")
    for c in checks:
        flag = "PASS" if c["passed"] else "FAIL"
        print(f"  [{flag}] {c['id']} {c['name']}")
        print(f"         {c['detail']}")
    print(f"ALL PASSED: {report['passed']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
