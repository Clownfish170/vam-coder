import json
import pytest
import catalog


def test_bad_price(tmp_path):
    p = tmp_path / "i.json"
    p.write_text(json.dumps({"k": {"price": "2"}}),
                 encoding="utf-8")
    with pytest.raises(ValueError):
        catalog.load(str(p))


def test_default_regression(tmp_path):
    p = tmp_path / "i.json"
    p.write_text(json.dumps({"k": {"title": "T"}}),
                 encoding="utf-8")
    assert catalog.load(str(p))["k"]["price"] == 0
