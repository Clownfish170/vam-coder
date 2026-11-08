import json
import tempfile

import config


def test_defaults():
    assert config.DEFAULTS["timeout_s"] == 45


def test_missing_key_fallback(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"retries": 2}), encoding="utf-8")
    assert config.load(str(p))["timeout_s"] == 45


def test_file_still_wins():
    assert config.load()["timeout_s"] == 60
