"""配置加载测试：config/default.json 与代码默认值的一致性。"""

from __future__ import annotations

import json
from pathlib import Path

from vam_coder.config import AppConfig

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON = PROJECT_ROOT / "config" / "default.json"


def test_default_json_exists_and_loads():
    assert DEFAULT_JSON.is_file()
    cfg = AppConfig.load(DEFAULT_JSON)
    assert cfg.closure_depth == 2
    assert cfg.hash_algo == "blake3"
    assert cfg.simulate_kv is True
    assert cfg.simulate_summary is True
    assert cfg.supported_languages == {".py": "python"}
    assert cfg.db_path == "state/static_store.db"
    assert cfg.decision_log == "logs/decisions.jsonl"
    assert cfg.invalidation_log == "logs/invalidation_events.jsonl"


def test_default_json_is_valid_json_with_separated_paths():
    raw = json.loads(DEFAULT_JSON.read_text(encoding="utf-8"))
    # 配置与源码分离：路径指向 config/ 之外的 logs/ 与 state/
    assert raw["paths"]["decision_log"].startswith("logs/")
    assert raw["paths"]["invalidation_log"].startswith("logs/")
    assert raw["paths"]["db"].startswith("state/")


def test_digest_deterministic_and_sensitive_to_routing_fields():
    a = AppConfig()
    b = AppConfig()
    assert a.digest() == b.digest()
    c = AppConfig(budget_tokens=128)
    assert a.digest() != c.digest()
    # 与路由无关的路径字段不影响 digest
    d = AppConfig(db_path="elsewhere.db")
    assert a.digest() == d.digest()
